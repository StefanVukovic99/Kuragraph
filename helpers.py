from os import listdir
from PIL import Image, ImageFont
import os
import cairo 
from constants import FONT_PATH

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

def toRGBfloat(RGBint):
    RGBfloat = [c/255 for c in RGBint]
    return tuple(RGBfloat)

def opacifyRGBint(RGBint):
    RGBint = [c/0.7-0.3*255 for c in RGBint]
    return toRGBfloat(RGBint)

def getDash(rikishiInfo):
    return rikishiInfo.get('dash', [])

def fontOfSize(size, fontPath = FONT_PATH):
    return ImageFont.truetype(fontPath, size)

def styledStroke(ctx, info, startWidth, endWidth, startOpacity, endOpacity, percentage):
    
    opacity = startOpacity + (endOpacity- startOpacity) * percentage
    width = startWidth + (endWidth- startWidth) * percentage

    ctx.set_source_rgba(*info['color'], opacity)
    ctx.set_line_width(width)
    #ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    #ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_dash(getDash(info))
    ctx.stroke()

lineStyles = [
    [],
    [8,2],
    [4, 2],
    [80, 15],
    [30, 5,5,5],
    [15,5,10,5,5,5], 
]