from utils import *
from world import *


import math
import uuid as uuidlib

RENDERDISTANCE = 3



class Player:
    def __init__(self, id, uuid, username, worker, x, y, grounded, z, yaw, pitch, just_spawned = 1, did_move = 1, did_pitchyaw = 1, running=1, doneupdatespeed = 1, onground = 1, active = 1):
        self.id = id
        self.uuid = uuid
        self.username = username
        self.x = x
        self.y = y
        self.grounded = grounded
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.chunk = False

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

        self.tickcounter = 25

        self.loaded_pillars = []

        self.oldx = self.x
        self.oldy = self.y
        self.oldz = self.z

        self.time = 0
       
        self.pitch = 0.5

    def tick(self):
        self.tickcounter += 1
        self.tick_since_update = 0
        
        if self.need_to_keep_alive and self.tickcounter > 20:
            self.send_keepalive()
            self.send_time()
            self.tickcounter = 0

        if self.need_to_respawn:
            self.send_player_list()
            self.respawn()
            self.need_to_respawn = False
            self.check_chunks()
            self.x = 0
            self.y = 16*2
            self.z = 0
            self.send_pos(self.x, self.y, self.z)

        self.check_chunks()

        #self.handle_moves()
        self.oldx = self.x
        self.oldy = self.y
        self.oldz = self.z
    
        self.sound_effect("block.note.pling", "block", 1.0, self.pitch)
        self.pitch += 0.2
        if self.pitch > 2:
            self.pitch = 0.5

    def respawn(self):
            self.change_camera(1337)
            print("sending spawn packet")
            self.worker.send_data(b'\x23', struct.pack(">i",1337), b'\x01', struct.pack(">i",0), b'\x01', b'\x08', "default", b'\x00') #spawn player
            self.worker.send_data(b'\x43', location(self.x, self.y, self.z))

    def spawn_teleport(self):
        print("spawn teleport")
        self.worker.send_data(b'\x49', pack_varint(1337), double(self.x), double(self.y), double(self.z), angle(self.yaw), angle(self.pitch), b'\x00')

    def send_pos(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z 
        self.worker.send_data(b'\x2e', double(self.x), double(self.y), double(self.z), gfloat(self.yaw), gfloat(self.pitch), b'\x07', pack_varint(0))
        print("sending pos")
        self.worker.send_data(b'\x1e', b'\x07', gfloat(0))

    def handle_moves(self):
        dx = self.x - self.oldx
        dy = self.y - self.oldy
        dz = self.z - self.oldz

        if abs(dx) > 4 or abs(dy) > 4 or abs(dz) > 8:
            self.worker.send_data(b'\x49', pack_varint(self.id), double(self.x), double(self.y), double(self.z), gfloat(self.yaw), gfloat(self.pitch), b'\x01' if self.grounded else b'\x00')    
        else:
            self.worker.send_data(b'\x26', pack_varint(self.id), deltapos(dx), deltapos(dy), deltapos(dz), gfloat(self.yaw), gfloat(self.pitch), b'\x01' if self.grounded else b'\x00')
        

    def send_pillar(self, x, z):
        for dx in range(-RENDERDISTANCE, RENDERDISTANCE):
            for dz in range(-RENDERDISTANCE, RENDERDISTANCE):
                if not [x+dx, z+dz] in self.loaded_pillars:
                    chunk = Chunk(x+dx,0,z+dz)
                    chunk.gen_chunk()
                    CHUNKDATA = generate_bedrock_chunk() + generate_chunk(chunk)
                    self.loaded_pillars.append([x+dx, z+dz])
                    print("sending pillar %s %s" %(x+dx, z+dz))
                    self.worker.send_data(b'\x20', struct.pack('>i', x + dx) , struct.pack('>i',z + dz), b'\x01', pack_varint(3), pack_varint(len(CHUNKDATA)), CHUNKDATA, pack_varint(0))
                    self.worker.send_data(b'\x0b', location((x+dx)* 16, 0, (z+dz)*16), pack_varint(0 << 4 | (0 & 15)))
                    self.need_to_keep_alive = 1
                    

    def check_chunks(self):
        x = math.floor(self.x/16)
        z = math.floor(self.z/16)
        self.send_pillar(x, z)

    

    def send_keepalive(self):
        self.alivecounter += 1
        self.worker.send_data(b'\x1f', pack_varint(self.alivecounter))
        #print("sending keepalive")
        if self.alivecounter > 25:
            self.alivecounter = 0
    
    def send_time(self):
        self.time += 20
        self.worker.send_data(b'\x44', struct.pack(">q", self.time), struct.pack(">q", self.time % 24000))
    
    def send_player_list(self):
        uuid = uuidlib.UUID(self.uuid)
        self.worker.send_data(b'\x2d', pack_varint(0), pack_varint(1), uuid.bytes, self.username, pack_varint(0), pack_varint(1), pack_varint(69), b'\x01', '{"text":"hello! ☠"}')

    def change_camera(self, target_entity_id):
        self.worker.send_data(b'\x36', pack_varint(target_entity_id))

    def sound_effect(self, sound_name, sound_cat, volume, pitch):
        self.worker.send_data('\x46', pack_varint(316), pack_varint(0), struct.pack('>i', math.floor(self.x*8)), struct.pack('>i', math.floor(self.y*8)), struct.pack('>i', math.floor(self.z*8)), gfloat(volume), gfloat(pitch));
