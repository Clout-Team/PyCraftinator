import sqlite3
import time
import struct

from utils import *

def generate_chunk(chunk):
    data = ''          
    d = "" 
    for f in range(4096):
        d += bin(chunk.data[f][0])[2:].zfill(9) + bin(chunk.data[f][1])[2:].zfill(4)
    d = [int(s, 2) for s in d]
    nd = []

    #print(d)
    for i in range(0, len(d), 64):
        out = 0
        for bit in d[i:i+64]:
            out = (out << 1) | bit 
        if i == 0:
            pass
            #print(d[i:i+64])
            #print(bin(out))
        nd.append(struct.pack(">q", (out % 2**64) - 2**64 if (out % 2**64)>=2**(63) else (out % 2**64)))
    #print(nd)
    light = [b'\xee' for i in range(2048)]
    return b'\x0d' + pack_varint(0) + pack_varint(len(nd)) + b''.join(nd[::-1]) +  b''.join(light) + b''.join(light)

def generate_air_chunk():
    nchunk = Chunk(0,0,0)
    nchunk.fill(0, 0)
    return generate_chunk(nchunk)

def generate_bedrock_chunk():
    nchunk = Chunk(1,1,0, [])
    nchunk.fill(12, 1)
    return generate_chunk(nchunk)

class Chunk:
    def __init__(self, x, y, z, data=[]):
        self.x = x
        self.y = y
        self.z = z
        self.data = data
    
    def fill(self, blockid, variantid):
        #fill left over space with blocks
        self.data.extend([[blockid, variantid] for i in range(4096 - len(self.data))])
    
    def to_bytes(self):
        #block id encoded as 3 byte long integers + variant id as 1 byte long char (both big endian)
        b = b''
        for i in self.data:
            b += struct.pack('>I', i[0])[1:]
            b += struct.pack('>B', i[1])
        return b
    
    def from_bytes(self, b):
        data = []
        for i in range(0, 4096*4, 4):
            data.append([struct.unpack('>I', b'\x00' + b[i:i+3])[0], int(b[i+3])])
        self.data = data
    
    def gen_chunk(self):
        self.fill(0, 0)
        for xi in range(16):
            for zi in range(16):
                s = perlin((self.x*16)+xi, ( self.z*16)+zi)
                for yi in range(int((1+s)*8)+2):
                    if yi < 16:
                        self.data[xi+16*zi+16*16*(15 - yi)] = [2, 0]
                       
        #for xi in range(16):
        #    for yi in range(16):
        #        for zi in range(16):
        #           if perlin(xi + self.x*16, yi + self.y*16, zi + self.z*16) > 0.42: 
        
        #if xi+yi*16+zi+16 < 4096:
        #self.data[xi+16*yi+16*16*zi] = [5, 5]
        #               else: 
        #                    print("data overflow")

class World:
    def __init__(self, name="world3", type=0):
        self.name = name
        self.filename = name + ".db"
        self.type = 0
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.filename)
        self._exec(('''CREATE TABLE IF NOT EXISTS chunks (x integer, z integer, y integer, data blob)''', ()))

    def _close(self):
        self.conn.close()
    
    def _exec(self, querylist):
        c = self.conn.cursor()
        if isinstance(querylist, list):
            for i in querylist:
                c.execute(querylist[i][0], querylist[i][1])
        else:
            c.execute(querylist[0], querylist[1])
        self.conn.commit()
    
    def _fetch(self, query, fetchtype = 0): 
        """fetchtype = 1 -> fetch all; 0 -> fetch one element (default)"""

        c = self.conn.cursor()
        c.execute(query)
        if not fetchtype:
            return c.fetchone()
        else:
            return c.fetchall()
    
    def get_chunk(self, x, y, z):
        d = self._fetch("select data from chunks where x = '%s' and y = '%s' and z = '%s'" %(x, y, z))[0]
        c = Chunk(x, y, z)
        c.from_bytes(d)
        return c
    
    def add_chunk(self, chunk):
        self._exec((("insert into chunks values (0, 0, 0, ?)", (sqlite3.Binary(chunk.to_bytes()),))))
    
