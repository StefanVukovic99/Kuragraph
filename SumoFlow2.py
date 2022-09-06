import cairo
from PIL import Image, ImageDraw, ImageFont
import math
from HatsuData import rikishi, kinboshi, sansho, basho
from helpers import checkFilesOfType, toRGBint, path, lineStyles, getDash, fontOfSize
from itertools import product, combinations
from datetime import datetime
import numpy as np

# imena
thumbnail = 160
margin = 150
baseFlowWidth = 12 
flowOpacity = 0.7;
fieldOpacity = 0.2
fieldRadius = 70

HEIGHT = 2*margin+15*thumbnail
WIDTH = HEIGHT + thumbnail * 8
step = (HEIGHT - 2 * margin) // 30
root = (margin, HEIGHT/2)

clusters = [{score: [] for score in range(-15, 16)} for day in range(15)]

for shikona, info in rikishi.items():
    for (day,p) in enumerate(info['record']):
        scoreTday = sum(info['record'][0:day+1])
        clusters[day][scoreTday].append(shikona);

def twistPrevent(day, score, shikona):
    
    rYday = rikishi[shikona]['record'][day] 
    posYday = clusters[day-1][score-rYday].index(shikona)
    result = -100 * rYday + posYday
    
    return result

def untangle():
    for (day, score) in product(range(15), range(-15, 16)):  
        
        lastDay = day == 14
        edgeField = abs(score) == day+1
        
        if(day != 0):
            clusters[day][score].sort(key = lambda s: twistPrevent(day, score, s))
        if(not lastDay):             
            clusters[day][score].sort(key = lambda s: s in clusters[day+1][score-1])
        if(not edgeField):
            clusters[day][score].sort(key = lambda s: s in clusters[day-1][score-1])

def countCrosses():
    print("counting crosses")
    gEnterCrosses = 0;
    gExitCrosses = 0;
    gTwists = 0;
    
    for (day, score) in product(range(15), range(-15, 16)):  
          
        cluster = clusters[day][score]
        
        edgeField = abs(score) == day+1
        lastDay = day == 14
        
        enterCrosses = 0
        exitCrosses = 0
        twists = 0
        
        for (shikona1, shikona2) in combinations(cluster, 2):
            if(not lastDay):
                
                r1Today = rikishi[shikona1]['record'][day+1] 
                r2Today = rikishi[shikona2]['record'][day+1]
                
                goingDown1 = r1Today == -1
                goingUp2 = r2Today == +1
                
                if(goingDown1 and goingUp2): 
                    exitCrosses += 1
                   
                if(r1Today == r2Today): 
                    nextCluster = clusters[day+1][score+r1Today]
                    if(nextCluster.index(shikona2) < nextCluster.index(shikona1)):
                        twists+=1
                    
            if(not edgeField):
                wasDown1 = shikona1 in clusters[day-1][score-1]
                wasUp2 = shikona2 in clusters[day-1][score+1]
                
                if(wasDown1 and wasUp2): 
                    enterCrosses += 1
                            
        gTwists += twists        
        gEnterCrosses += enterCrosses
        gExitCrosses += exitCrosses
        
    print("gEnterCrosses", gEnterCrosses, "gExitCrosses", gExitCrosses, "gTwists", gTwists, "total", gExitCrosses+gEnterCrosses+gTwists)


def createSurface():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT,)
      
    ctx = cairo.Context(surface)
    
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()
    
    print("Surface created")
    return ctx, surface

def drawFields():
    for day in range(16):
        for nOfWins in range(day+1):
            ctx.arc(margin+day*2*step, HEIGHT/2+day*step-nOfWins*2*step, fieldRadius, 0, 2*math.pi)
            fieldHue=(0.65,0.59,0.4)
            if(nOfWins>=8): fieldHue=(0,1,0)
            if(day-nOfWins>=8): fieldHue=(1,0,0)
            
            ctx.set_source_rgba(*fieldHue, fieldOpacity)
            ctx.fill()
    print("Fields drawn")
       
def styledStroke(ctx, info, width, opacity):
     ctx.set_source_rgba(*info['color'], opacity)
     ctx.set_line_width(width)
     #ctx.set_line_cap(cairo.LINE_CAP_ROUND)
     ctx.set_dash(getDash(info))
     ctx.stroke()
     
def drawFlows(): 
    for shikona, info in rikishi.items():
        ctx.move_to(*root)
        nextPoint = [*root]
        for (day,p) in enumerate(info['record']):
            
            flowWidth = (0.5+0.5*day/14)*baseFlowWidth
            
            scoreTday = sum(info['record'][0:day+1])
            
            clusterSize = len(clusters[day][scoreTday])
            posInCluster = clusters[day][scoreTday].index(shikona)
            yOffset = (clusterSize/2 - 0.5 - posInCluster) * flowWidth * 1.3
            
            nowPoint = nextPoint
            nextY = root[1]- scoreTday * step - yOffset
            nextPoint = [nowPoint[0] + step*2, nextY]
            controlPoint1 = [nowPoint[0] + step, nowPoint[1]]
            controlPoint2 = [nextPoint[0] - step, nextPoint[1]]
                        
            ctx.curve_to(*controlPoint1, *controlPoint2, *nextPoint)
            
            opacity = flowOpacity
            if(info.get('kyujo') and day in info.get('kyujo')): opacity= 0
                
            styledStroke(ctx, info, flowWidth, opacity)
            
            ctx.move_to(*nextPoint)
    
    filename = "Hatsu_2022_v2_flows_only.png"

    surface.write_to_png(filename)
    
    print("Flows drawn")
    return filename

def markPortrait(shikona, info):
    portrait = cairo.ImageSurface.create_from_png(shikona+".png")
    ctx = cairo.Context(portrait)
    
    ctx.move_to(15, 15)
    ctx.curve_to(*(15, 80), *(15, 80), *(15, 145))
    styledStroke(ctx, info, baseFlowWidth, flowOpacity)
    
    tmpFilename = "tmpFile.png"
    
    offset = 0
    if(info.get('banzukeD')):
        
        color = info['banzukeD']['color']
        
        
        if (color == (0.8, 1, 0.8, 1)): offset = 2.5
        if (color == (1, 0.8, 0.8, 1)): offset = -2.5
        
        ctx.move_to(145, 152.5 + offset)
        ctx.line_to(145, 137.5 + offset)
        ctx.line_to(132.5, 135)
        ctx.line_to(120, 137.5 + offset)
        ctx.line_to(120, 152.5 + offset)
        ctx.line_to(132.5, 155)
        ctx.close_path()
        ctx.set_source_rgba(*color)
        ctx.fill_preserve()    
        ctx.set_line_width(0.04)
        ctx.stroke()
        
    portrait.write_to_png(tmpFilename)
    
    markedPortrait = Image.open(path(tmpFilename)).convert(mode='RGBA')
    
    overlay = Image.new('RGBA', markedPortrait.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    if(info.get('banzukeD')):
        draw.text((132.5, 145+offset), info['banzukeD']['text'], fill=(0,0,0,200), font=fontOfSize(14), anchor="mm")

    if(sansho.get(shikona)):   
        color = toRGBint((*(0.86, 0.77, 0.16), flowOpacity))
        draw.ellipse((114, 6, 154, 46), fill = color, outline = color)
        draw.text((134, 26), sansho[shikona], fill=(0,0,0,200), font=fontOfSize(30), anchor="mm")
        
    markedPortrait = Image.alpha_composite(markedPortrait, overlay)  
    
    
        
    return markedPortrait
    
    
def drawPortraits(portraitlessFile):
    background = Image.open(path(portraitlessFile))
    
    koshi = {score: 0 for score in range(-15, 16, 2)}
    
    for shikona, info in rikishi.items():
        
        markedPortrait = markPortrait(shikona, info)
        
        score = sum(info['record'])
        
        offset = (margin+31*step+koshi[score]*thumbnail, HEIGHT//2 - step*score - thumbnail//2)
        background.paste(markedPortrait, offset)
        koshi[score]+=1;
    
    filename = 'Hatsu_2022_v2_no_text.png'
    background.save(filename)
    
    print("Portraits drawn")
    return filename

def writeText(textless_file):
    textlessGraph = Image.open(path(textless_file)).convert(mode='RGBA')
    txtLayer = Image.new('RGBA', textlessGraph.size, (255,255,255,0))
    draw = ImageDraw.Draw(txtLayer)    
    fill =(0,0,0,200)
    
    draw.text((WIDTH-650, 200), basho, font=fontOfSize(128), fill=fill, anchor="mm")
    draw.text((WIDTH-650, 350), "クラグラフ", font=fontOfSize(128), fill=fill, anchor="mm")

    
    draw.text((50, HEIGHT-50), "Kuragraph " + basho + ' ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), font=fontOfSize(12), fill=fill)
    
    for day in range(1,16):
    
        text = f"{day}日"
        xPos = margin+day*2*step - len(text)/2 * 20
        draw.text((xPos, HEIGHT/2-day*step-fieldRadius - 40), text, font=fontOfSize(24), fill=fill)
        draw.text((xPos, HEIGHT/2+day*step+fieldRadius), text, font=fontOfSize(24), fill=fill)
        
    for wins in range(0,16):
        lastDayX = margin + 30 * step + fieldRadius * 0.4
        lastDayY = HEIGHT - margin - wins * step * 2
        draw.text((lastDayX, lastDayY - fieldRadius/2), str(wins), font=fontOfSize(24), fill=fill, anchor='mm')
        draw.text((lastDayX, lastDayY), "|", font=fontOfSize(24), fill=fill, anchor='mm')
        draw.text((lastDayX, lastDayY + fieldRadius/2), str(15-wins), font=fontOfSize(24), fill=fill, anchor='mm')

    graphWithText = Image.alpha_composite(textlessGraph, txtLayer)    
    
    filename = 'Hatsu_2022_with_text.png'
    graphWithText.save(filename)
    print("Text written")
    return graphWithText

def drawKinboshi(starlessGraph):
        
    star = Image.open(path('kinboshi.svg'))
    
    wpercent = (20/float(star.size[0]))
    hsize = int((float(star.size[1])*float(wpercent)))
    star = star.resize((20,hsize), Image.ANTIALIAS).convert(mode='RGBA')
    
    for hoshi in kinboshi:
        
        shikona = hoshi[0]
        day = hoshi[1]
        
        flowWidth = (0.5+0.5*day/14)*baseFlowWidth

        info = rikishi[shikona]
        
        scoreTday = sum(info['record'][0:day])
        
        clusterSize = len(clusters[day-1][scoreTday])
        posInCluster = clusters[day-1][scoreTday].index(shikona)
        yOffset = (clusterSize/2 - 0.5 - posInCluster) * flowWidth * 1.3

        nextY = root[1]- scoreTday * step - yOffset
        hoshiPoint = [root[0]+day*2*step, nextY]
                
        starlessGraph.paste(star, tuple([round(c)-10 for c in hoshiPoint]), star)
        
    filename = 'Hatsu_2022_with_stars.png'
    starlessGraph.save(filename)
    print("Stars drawn")
    return filename

def countColorCollisions():
    colorCollisions = {shikona:[] for shikona in rikishi}
    for s1, s2 in product(rikishi.keys(), rikishi.keys()):
        
        color1 = flowOpacity*np.array([rikishi[s1]['color']])+(1-flowOpacity)*np.array((1,1,1))
        color2 = flowOpacity*np.array([rikishi[s2]['color']])+(1-flowOpacity)*np.array((1,1,1))
        
        colorsDistance = np.linalg.norm(color1-color2)
            
        if(not s1==s2 and colorsDistance <= 0.158): #max 0.158 zbog Ura i Koteko
            colorCollisions[s1].append(s2)
            
    if(max(len(c) for c in colorCollisions.values()) > len(lineStyles)): print("Color collisions unavoidable!")
    
    return colorCollisions

def avoidColorCollisions():
    globalStyleHist = [0] * len(lineStyles)
    globalStyleHist[0] = len(rikishi)
    for s1 in rikishi:
        colorCollisions = countColorCollisions()
        collisions = filter(lambda s2: (sum(rikishi[s2]['record']) == sum(rikishi[s1]['record'])), colorCollisions[s1])
        collisions = list(collisions)
        if(len(collisions)):
            sameColorHist = [0] * len(lineStyles)
            for s2 in collisions:
                sameColorHist[lineStyles.index(getDash(rikishi[s2]))]+=1
            myStyleIndex = sameColorHist.index(min(sameColorHist))
            rikishi[s1]['dash'] = lineStyles[myStyleIndex]
            globalStyleHist[myStyleIndex]+=1
            globalStyleHist[0]-=1
    print(globalStyleHist)
            
avoidColorCollisions()

untangle()
countCrosses()

checkFilesOfType('png')

ctx, surface = createSurface()

drawFields()

fieldsAndFlows = drawFlows()

textlessGraph = drawPortraits(fieldsAndFlows)

starlessGraph = writeText(textlessGraph)

drawKinboshi(starlessGraph)

    
print("Kuragraph complete!")