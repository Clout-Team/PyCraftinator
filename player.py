from utils import *


data = ''          
d = "" 
for x in range(0, 4096):
    d += bin(2)[2:].zfill(9) + bin(0 & 0x0F)[2:].zfill(4)
d = [int(s) for s in d]
nd = []
for i in range(0, len(d), 64):
    out = 0
    for bit in reversed(d[i:i+64]):
        out = (out << 1) | bit
    nd.append(struct.pack("<Q", out))

light = [b'\xee' for i in range(0, 2048)]
data = b'\x0d' + pack_varint(0) + pack_varint(len(nd)) + b''.join(nd) + b''.join(light) + b''.join(light)

class Player:
    def __init__(self, worker, x, y, stance, z, yaw, pitch, just_spawned = 1, did_move = 1, did_pitchyaw = 1, running=1, doneupdatespeed = 1, onground = 1, active = 1):
        self.x = x
        self.y = y
        self.stance = stance
        self.z = z
        self.yaw = yaw
        self.pitch = pitch

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

    def tick(self):
        self.tick_since_update = 0
        if self.need_to_respawn:
            self.x = 0
            self.y = 17
            self.stance = 0
            self.z = 0
            self.send_pos()
            self.need_to_respawn = False
        self.send_chunk()
    def send_pos(self):
        self.worker.send_data(b'\x2e', double(self.x), double(self.y), double(self.z), float(self.yaw), float(self.pitch), b'\x00', pack_varint(0))
        print("sending pos")  
        self.send_chunk()

    def send_chunk(self):
        self.worker.send_data(b'\x20', struct.pack('i',0) , struct.pack('i',0), b'\x01', b'\x01', pack_varint(len(data)), data, pack_varint(0))
