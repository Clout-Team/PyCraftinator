from utils import *
from world import *

import math

RENDERDISTANCE = 10

class Player:
    def __init__(self, id, worker, x, y, grounded, z, yaw, pitch, just_spawned = 1, did_move = 1, did_pitchyaw = 1, running=1, doneupdatespeed = 1, onground = 1, active = 1):
        self.id = id
        self.x = x
        self.y = y
        self.grounded = grounded
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.chunk = []

        self.just_spawned = just_spawned
        self.did_move = did_move
        self.did_pitchyaw = did_pitchyaw
    
        self.running = running
        self.doneupdatespeed = doneupdatespeed

        self.onground = onground
        self.active = active
        self.has_logged_on = 1

        self.worker = worker
        self.username = worker.username

        self.ticks_since_update = 1
        self.ticks_since_heard = 1

        self.next_chunk_to_load = 1
        
        self.need_to_respawn = 0
        
        self.need_to_keep_alive = 0
        self.alivecounter = 0

        self.tickcounter = 0

        self.loaded_pillars = []

        self.oldx = self.x
        self.oldy = self.y
        self.oldz = self.z

    def tick(self, chunk):
        self.chunk = chunk
        self.tickcounter += 1
        self.tick_since_update = 0


        if self.need_to_respawn:
            print("sending spawn packet")
            self.worker.send_data(b'\x23', struct.pack("i",1337), b'\x01', struct.pack("i",0), b'\x01', b'\x08', "default", b'\x00') #spawn player
            self.x = 0
            self.y = 16*2
            self.z = 0
            self.send_pos(self.x, self.y, self.z)
            self.need_to_respawn = False

        if self.need_to_keep_alive and self.tickcounter > 25:
            self.send_keepalive()
            self.tickcounter = 0

        
        self.check_chunks()
        #self.handle_moves()
        self.oldx = self.x
        self.oldy = self.y
        self.oldz = self.z

    def send_pos(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z 
        self.worker.send_data(b'\x2e', double(self.x), double(self.y), double(self.z), gfloat(self.yaw), gfloat(self.pitch), b'\x07', pack_varint(0))
        print("sending pos")  

    def handle_moves(self):
        dx = self.x - self.oldx
        dy = self.y - self.oldy
        dz = self.z - self.oldz

        if abs(dx) > 4 or abs(dy) > 4 or abs(dz) > 8:
            self.worker.send_data(b'\x49', pack_varint(self.id), double(self.x), double(self.y), double(self.z), gfloat(self.yaw), gfloat(self.pitch), b'\x01' if self.grounded else b'\x00')    
        else:
            self.worker.send_data(b'\x26', pack_varint(self.id), deltapos(dx), deltapos(dy), deltapos(dz), gfloat(self.yaw), gfloat(self.pitch), b'\x01' if self.grounded else b'\x00')
        

    def send_pillar(self, x, z):
        for dx in range(RENDERDISTANCE):
            for dz in range(RENDERDISTANCE):
                if not [x+dx, z+dz] in self.loaded_pillars:
                    self.loaded_pillars.append([x+dx, z+dz])
                    print("sending pillar %s %s" %(x+dx, z+dz))
                    data = b''
                    data += generate_bedrock_chunk() + generate_chunk(self.chunk) 
                    self.worker.send_data(b'\x20', struct.pack('>i',-2 + x + dx) , struct.pack('>i',-2 + z + dz), b'\x01', pack_varint(3), pack_varint(len(data)), data,  pack_varint(0))
                    self.need_to_keep_alive = 1
                    

    def check_chunks(self):
        x = math.floor(self.x/16)
        z = math.floor(self.z/16)
        if not [x, z] in self.loaded_pillars:
            self.send_pillar(x, z)

    

    def send_keepalive(self):
        self.alivecounter += 1
        self.worker.send_data(b'\x1f', pack_varint(self.alivecounter))
        #print("sending keepalive")
        if self.alivecounter > 25:
            self.alivecounter = 0

