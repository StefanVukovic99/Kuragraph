import cairo
from PIL import Image, ImageDraw
import os
from os import listdir
import math
import HatsuData

dir = os.path.dirname(__file__)

def checkFilesOfType(filetype):
    for filename in listdir('./'):
      if filename.endswith('.'+filetype):
        try:
          img = Image.open('./'+filename) # open the image file
          img.verify() # verify that it is, in fact an image
        except (IOError, SyntaxError) as e:
          print('Bad file:', filename, e)
          
def path(filename):
    return os.path.join(dir, filename)

def toRGBint(RGBfloat):
    RGBint = [round(255.0*c) for c in RGBfloat]
    return tuple(RGBint)
          

rikishi = HatsuData.rikishi;

margin = 150
thumbnail = 160
HEIGHT = 2*margin+15*thumbnail
WIDTH = HEIGHT + thumbnail * 8
step = (HEIGHT - 2 * margin) // 30
flowOpacity = 0.7;
flowWidth = 12  
breakeven = (50,10)

checkFilesOfType('png')
    
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT,)
  
ctx = cairo.Context(surface)

ctx.rectangle(0, 0, WIDTH, HEIGHT)
ctx.set_source_rgb(1, 1, 1)
ctx.fill()

for day in range(16):
    for nOfWins in range(day+1):
        ctx.arc(margin+day*2*step, HEIGHT/2+day*step-nOfWins*2*step, 50, 0, 2*math.pi)
        fieldHue=(0.65,0.59,0.4)
        if(nOfWins>=8): fieldHue=(0,1,0)
        if(day-nOfWins>=8): fieldHue=(1,0,0)
        
        ctx.set_source_rgba(*fieldHue, 0.2)
        ctx.fill()

dailyKoshiA = [{score: 0 for score in range(-15, 16, 1)} for _ in range(15)]
dailyKoshiB = [{score: 0 for score in range(-15, 16, 1)} for _ in range(15)]

for shikona, info in rikishi.items():
    for (i,p) in enumerate(info['record']):
        dailyKoshiA[i][sum(info['record'][0:i+1])] += 1
    
for shikona, info in rikishi.items():
    ctx.move_to(margin, HEIGHT/2)
    x,y=ctx.get_current_point()
    for (i,p) in enumerate(info['record']):
        
        x=margin+i*step*2
        y=HEIGHT/2-sum(info['record'][0:i])*step
        
        flowWidthNow = (0.5+0.5*i/14)*flowWidth
        
        overlaps = dailyKoshiA[i][sum(info['record'][0:i+1])]
        yOffset = (dailyKoshiB[i][sum(info['record'][0:i+1])] + overlaps/2 - 0.5) * flowWidthNow * 1.1
        

        ctx.curve_to(x+step, y+yOffset, x+step, y-p*step+yOffset, x+step*2, y-p*step+yOffset)
        ctx.set_source_rgba(*info['color'], flowOpacity)
        ctx.set_line_width(flowWidthNow)
        ctx.stroke()
        
        ctx.move_to(x+step*2, y-p*step+yOffset)

        dailyKoshiB[i][sum(info['record'][0:i+1])] -= 1
        
    

'''ctx.rectangle(margin+30*step-breakeven[0]//2, HEIGHT/2-breakeven[1]//2, *breakeven)
ctx.set_source_rgb(0, 0, 0)
ctx.fill()'''


surface.write_to_png("Hatsu_2022.png")
    
print("File Saved")

background = Image.open(path("Hatsu_2022.png"))

koshi = {score: 0 for score in range(-15, 16, 2)}

for shikona, info in rikishi.items():
    
    img = Image.open(path(shikona+".png"))
    
    wpercent = (thumbnail/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((thumbnail,hsize), Image.ANTIALIAS).convert(mode='RGBA')
    
    '''draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 40, 40), fill = color, outline = color)'''
    
    color = toRGBint((*info['color'], flowOpacity))
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((0, 0, 40, 40), fill = color, outline = color) 
    
    img = Image.alpha_composite(img, overlay)

    score = sum(info['record'])
    
    bg_w, bg_h = background.size
    offset = (margin+31*step+koshi[score]*thumbnail, bg_h//2 - step*score - thumbnail//2)
    background.paste(img, offset)
    koshi[score]+=1;
    
background.save('out.png')
