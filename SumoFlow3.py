import cairo
from PIL import Image, ImageDraw
import math
from itertools import product, combinations
from datetime import datetime
import numpy as np

from Data_202207 import bashoName, DAYS, rikishi, kinboshi, sansho, YUSHO
#from HatsuData import bashoName, DAYS, rikishi, kinboshi, sansho
from helpers import checkFilesOfType, toRGBint, path, lineStyles, getDash, fontOfSize, styledStroke
from constants import THUMBNAIL, MARGIN, BASE_FLOW_WIDTH, FLOW_OPACITY, FIELD_OPACITY, FIELD_RADIUS, FLOW_WIDTH_ROC

clusters = [{score: [] for score in range(-DAYS, DAYS+1)} for day in range(DAYS)]

for shikona, info in rikishi.items():
    for (day,p) in enumerate(info['record']):
        scoreTday = sum(info['record'][0:day+1])
        print(day, scoreTday, shikona)
        clusters[day][scoreTday].append(shikona);

histMode = max([len(lastCluster) for lastCluster in clusters[DAYS-1].values()])

HEIGHT = 2*MARGIN+DAYS*THUMBNAIL
step = THUMBNAIL/2 * math.sqrt(3)/2
WIDTH = int(2*MARGIN + DAYS * 2 * step + THUMBNAIL * histMode)
root = (MARGIN, HEIGHT/2)
ABS_MAX_WIDTH = FIELD_RADIUS * 0.26

def twistPrevent(day, score, shikona):
    
    rTday = rikishi[shikona]['record'][day] 
    posYday = clusters[day-1][score-rTday].index(shikona)
    result = 100 * rTday + posYday
    
    return result

def twistPreventBackwards(day, score, shikona):
    rTommorow = rikishi[shikona]['record'][day+1] 
    posTmorrow = clusters[day+1][score+rTommorow].index(shikona)
    result = -100 * rTommorow + posTmorrow
    
    return result

def untangleTwists(day, score):
    isFirstDay = day == 0
    if(not isFirstDay):
        clusters[day][score].sort(key = lambda s: twistPrevent(day, score, s))
        
def untangleTwistsBackwards(day, score):
    isLastDay = day == DAYS-1
    if(not isLastDay):
        clusters[day][score].sort(key = lambda s: twistPreventBackwards(day, score, s))
        
def untangleExits(day, score):
    isLastDay = day == DAYS-1
    if(not isLastDay):             
        clusters[day][score].sort(key = lambda s: s in clusters[day+1][score-1])

def untangleEntrances(day, score):
    isEdgeField = abs(score) == day+1
    if(not isEdgeField):
        clusters[day][score].sort(key = lambda s: s in clusters[day-1][score-1])
        
def untangle():
    for (day, score) in product(range(DAYS), range(-DAYS, DAYS+1)):  
        
        untangleTwists(day, score)
        untangleExits(day, score)
        untangleEntrances(day, score)
          
    for (day, score) in product(range(DAYS-1, -1, -1), range(-DAYS, DAYS+1)):  
        untangleTwistsBackwards(day, score)
        
def countLocalCrosses(day, score):
    cluster = clusters[day][score]
    
    edgeField = abs(score) == day+1
    lastDay = day == DAYS - 1
    
    enterCrosses = twists =  exitCrosses = 0
    
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
    return enterCrosses, exitCrosses, twists
    
def countCrosses():
    print("counting crosses")
    
    gEnterCrosses = gExitCrosses = gTwists = 0
    
    for (day, score) in product(range(DAYS), range(-DAYS, DAYS+1)):  
          
        enterCrosses, exitCrosses, twists = countLocalCrosses(day, score)
                            
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
    for day in range(DAYS+1):
        for nOfWins in range(day+1):
            ctx.arc(MARGIN+day*2*step, HEIGHT/2+day*THUMBNAIL/2-nOfWins*THUMBNAIL, FIELD_RADIUS, 0, 2*math.pi)
            fieldHue=(0.65,0.59,0.4)
            if(nOfWins>=8): fieldHue=(0,1,0)
            if(day-nOfWins>=8): fieldHue=(1,0,0)
            
            ctx.set_source_rgba(*fieldHue, FIELD_OPACITY)
            ctx.fill()
    print("Fields drawn")
    
def scoreOnDay(shikona, day):
    return sum(rikishi[shikona]['record'][0:day+1])

def clusterOnDay(shikona, day):
    return clusters[day][scoreOnDay(shikona, day)]

def getGutterWidth(shikona, day):
# =============================================================================
#     return (0.5+0.5*day/14) * BASE_FLOW_WIDTH * GUTTER_SHARE
# =============================================================================
    clusterSize = len(clusterOnDay(shikona, day))

    return (2*FIELD_RADIUS*0.90) / clusterSize * 0.3

def getYoffset(shikona, day):
    
    flowWidth = getFlowWidth(shikona, day)
            
    cluster = clusterOnDay(shikona, day)
    
    posInCluster = cluster.index(shikona)
    
    gutterWidth = getGutterWidth(shikona, day)
    
    sheafThickness = sum([getFlowWidth(s, day) + gutterWidth for s in cluster])
    thicknessAbove = sum([getFlowWidth(s, day) + gutterWidth for s in cluster[:posInCluster]])
    centerOffset = (flowWidth + gutterWidth) / 2
        
    yOffset = sheafThickness/2 - thicknessAbove - centerOffset

    return yOffset
    
def getPoint(shikona, day):
    
    scoreTday = scoreOnDay(shikona, day)

    yOffset = getYoffset(shikona, day)

    nextY = root[1]- scoreTday * THUMBNAIL/2 - yOffset
    nextPoint = [root[0]+(day+1)*2*step, nextY]
        
    return nextPoint

def getFieldSizeLimit(shikona, day):
    clusterSize = len(clusterOnDay(shikona, day))
    fieldSizeLimit = (2*FIELD_RADIUS*0.90) / clusterSize - getGutterWidth(shikona, day)
    return fieldSizeLimit

def maxWidth(shikona, day):
    
    fieldSizeLimit = getFieldSizeLimit(shikona, day)
    
    kyujoLimit = FIELD_RADIUS/7 if isKyujo(shikona, day) else ABS_MAX_WIDTH
    
    return min(fieldSizeLimit, ABS_MAX_WIDTH, kyujoLimit)
    
def maxWidthLeft(shikona, day):
    maxWidthN = maxWidth(shikona, day)
    if(day==0):
        return maxWidthN
    else:
        return min(FLOW_WIDTH_ROC * maxWidthLeft(shikona, day-1), maxWidthN)
    
def maxWidthRight(shikona, day):
    maxWidthN = maxWidth(shikona, day)
    if(day==DAYS-1):
        return maxWidthN
    else:
        return min(FLOW_WIDTH_ROC * maxWidthRight(shikona, day+1), maxWidthN)
    
def getFlowWidth(shikona, day):
    
    maxWidthN = maxWidth(shikona, day)
    maxWidthL = maxWidthLeft(shikona, day)
    maxWidthR = maxWidthRight(shikona, day,)
        
    return min (maxWidthL, maxWidthN, maxWidthR)

def hasKyujo(shikona):
    return rikishi[shikona].get('kyujo') 

def isKyujo(shikona, day):
    return hasKyujo(shikona) and day in rikishi[shikona]['kyujo']

def getOpacity(shikona, day):
    if(isKyujo(shikona, day)): 
        return FLOW_OPACITY * 0.2
    else:
        return FLOW_OPACITY


def halveCubicBezier(A, B, C, D):
    
    A = np.array(A)
    B = np.array(B)
    C = np.array(C)
    D = np.array(D)
    
    E = (A+B)/2
    F = (B+C)/2
    G = (C+D)/2
    H = (E+F)/2
    J = (F+G)/2
    K = (H+J)/2
    
    bezier1 = (A,E,H,K)
    bezier2 = (K,J,G,D)
    
    bezier1 = tuple([tuple(point) for point in bezier1])
    bezier2 = tuple([tuple(point) for point in bezier2])

    return bezier1, bezier2
    
def splitCubicBezier(A, B, C, D, nOfParts):
    
    if(nOfParts == 1): return [(A,B,C,D)]
    else:
        part1, part2 = halveCubicBezier(A, B, C, D)
        part1 = splitCubicBezier(*part1, nOfParts/2)
        part2 = splitCubicBezier(*part2, nOfParts/2)

    return [*part1, *part2]
        
def drawFlows(): 
    for shikona, info in rikishi.items():
        nextPoint = [*root]
        for (day,p) in enumerate(info['record']):
            
            ctx.move_to(*nextPoint)
            
            nowPoint = nextPoint  
            nextPoint = getPoint(shikona, day)
            
            controlPoint1 = [nowPoint[0] + step, nowPoint[1]]
            controlPoint2 = [nextPoint[0] - step, nextPoint[1]]
            
            nSections = 8
                        
            bezierCurves = splitCubicBezier(nowPoint, controlPoint1, controlPoint2, nextPoint, nSections)
            
            for (i, cubicBezier) in enumerate(bezierCurves):
            
                A,B,C,D = cubicBezier

                ctx.move_to(*A)
                ctx.curve_to(*B, *C, *D)
                
                percentage = (i+1)/nSections
                
                startWidth = 0 if day == 0 else getFlowWidth(shikona, day-1)
                endWidth = getFlowWidth(shikona, day)
                
                startOpacity = getOpacity(shikona, day-1)
                endOpacity = getOpacity(shikona, day)
                
                styledStroke(ctx, info, startWidth, endWidth, startOpacity, endOpacity, percentage)
    
    filename = "flows_only.png"

    surface.write_to_png(filename)
    
    print("Flows drawn")
    return filename

def markBanzukeD(draw, offset, text):
    draw.text((132.5, 145+offset), text, fill=(0,0,0,200), font=fontOfSize(14), anchor="mm")
    
def markPortrait(shikona, info):
    portrait = cairo.ImageSurface.create_from_png(path(f"Portraits/{shikona}.png"))
    ctx = cairo.Context(portrait)
    
    startPoint = [15, 15]
    cP1 = [15, 55]
    cP2 = [15, 105]
    endPoint = [15, 145]
    
    bezierCurves = splitCubicBezier(startPoint, cP1, cP2, endPoint, 8)
    
    for (i, cubicBezier) in enumerate(bezierCurves):
        A,B,C,D = cubicBezier

        ctx.move_to(*A)
        ctx.curve_to(*B, *C, *D)
        
        percentage = (i+1)/8
        endOpacity = FLOW_OPACITY * 0.2 if hasKyujo(shikona) else FLOW_OPACITY
        styledStroke(ctx, info, BASE_FLOW_WIDTH, BASE_FLOW_WIDTH, FLOW_OPACITY, endOpacity, percentage)
    
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
      
    tmpFilename = "tmpFile.png"
    portrait.write_to_png(tmpFilename)
    
    markedPortrait = Image.open(path(tmpFilename)).convert(mode='RGBA')
    
    
    overlay = Image.new('RGBA', markedPortrait.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    if(info.get('banzukeD')):
        markBanzukeD(draw, offset, info['banzukeD']['text'])

    if(sansho.get(shikona)):   
        color = toRGBint((*(0.86, 0.77, 0.16), FLOW_OPACITY))
        draw.ellipse((114, 6, 154, 46), fill = color, outline = color)
        draw.text((134, 26), sansho[shikona], fill=(0,0,0,200), font=fontOfSize(30), anchor="mm")
        
    markedPortrait = Image.alpha_composite(markedPortrait, overlay)  
    
    return markedPortrait
    
def drawPortraits(portraitlessFile):
    background = Image.open(path(portraitlessFile))
        
    for shikona, info in rikishi.items():
        
        markedPortrait = markPortrait(shikona, info)
        
        score = scoreOnDay(shikona, DAYS-1)
        posOn14 = clusterOnDay(shikona, DAYS-1).index(shikona)
        
        offsetX = int(MARGIN+(DAYS*2+1)*step+posOn14*THUMBNAIL)
        offsetY = int((HEIGHT - THUMBNAIL * (score+1))/2)
        background.paste(markedPortrait, (offsetX, offsetY))
            
    filename = 'no_text.png'
    background.save(filename)
    
    print("Portraits drawn")
    return filename

def writeText(textless_file):
    textlessGraph = Image.open(path(textless_file)).convert(mode='RGBA')
    txtLayer = Image.new('RGBA', textlessGraph.size, (255,255,255,0))
    draw = ImageDraw.Draw(txtLayer)    
    fill =(0,0,0,200)
        
    draw.text((WIDTH-550, 200), bashoName, font=fontOfSize(128), fill=fill, anchor="mm")
    draw.text((WIDTH-550, 350), "幕内優勝争い", font=fontOfSize(128), fill=fill, anchor="mm")
    draw.text((WIDTH-550, 500), "クラグラフ", font=fontOfSize(128, "./Rampart_One/RampartOne-Regular.ttf"), fill=fill, anchor="mm")

    draw.text((50, HEIGHT-50), "Kuragraph " + bashoName + ' ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), font=fontOfSize(12), fill=fill)
    
    for day in range(1,16):
    
        text = f"{day}日"
        xPos = MARGIN+day*2*step - len(text)/2 * 20
        draw.text((xPos, HEIGHT/2-day*THUMBNAIL/2-FIELD_RADIUS - 40), text, font=fontOfSize(24), fill=fill)
        draw.text((xPos, HEIGHT/2+day*THUMBNAIL/2+FIELD_RADIUS), text, font=fontOfSize(24), fill=fill)
        
    for wins in range(DAYS+1):
        lastDayX = MARGIN + DAYS*2 * step + FIELD_RADIUS * 0.4
        lastDayY = HEIGHT - MARGIN - wins * THUMBNAIL
        draw.text((lastDayX, lastDayY - FIELD_RADIUS/2), str(wins), font=fontOfSize(24), fill=fill, anchor='mm')
        draw.text((lastDayX, lastDayY), "|", font=fontOfSize(24), fill=fill, anchor='mm')
        draw.text((lastDayX, lastDayY + FIELD_RADIUS/2), str(DAYS-wins), font=fontOfSize(24), fill=fill, anchor='mm')

    graphWithText = Image.alpha_composite(textlessGraph, txtLayer)    
    
    filename = 'with_text.png'
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

        hoshiPoint = getPoint(shikona, day)
                
        starlessGraph.paste(star, tuple([round(c)-10 for c in hoshiPoint]), star)
        
    filename = f'{bashoName}.png'
    starlessGraph.save(filename)
    print("Stars drawn")
    return filename

def countColorCollisions():
    colorCollisions = {shikona:[] for shikona in rikishi}
    for s1, s2 in product(rikishi.keys(), rikishi.keys()):
                
        color1 = FLOW_OPACITY*np.array([rikishi[s1]['color']])+(1-FLOW_OPACITY)*np.array((1,1,1))
        color2 = FLOW_OPACITY*np.array([rikishi[s2]['color']])+(1-FLOW_OPACITY)*np.array((1,1,1))
        
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
       
def elevateChampion():
    if (DAYS == 15):
        for score in range(-DAYS, DAYS+1):
            clusters[14][score].sort(key = lambda s: s != YUSHO)
            
avoidColorCollisions()
untangle()
elevateChampion()

countCrosses()


checkFilesOfType('png')

ctx, surface = createSurface()

drawFields()

fieldsAndFlows = drawFlows()

textlessGraph = drawPortraits(fieldsAndFlows)

starlessGraph = writeText(textlessGraph)

drawKinboshi(starlessGraph)

print("Kuragraph complete!")

print(DAYS)