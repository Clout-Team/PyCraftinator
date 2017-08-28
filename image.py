import PIL
from PIL import Image

import re

import world
from world import Chunk

def generate_heart_chunk(filename = "heart.png", blockid=[35, 14]):

    im = Image.open(filename)
    im.thumbnail((16, 16), Image.ANTIALIAS)
    imdata = list(im.getdata())
    #print(list(im.getdata()))
    data = []
    
    pngtype = re.compile(".*\.png") 
    
    if pngtype.match(filename):
        for i in imdata:
            if i[3] > 50:
                data.append(blockid)
            else:
                data.append([0,0])
    else:
        for i in imdata:
            if i[2] > 50:
                data.append(blockid)
            else:
                data.append([0,0])

    chunk = Chunk(0,0,0, data)
    chunk.fill(0,0)
    return chunk

