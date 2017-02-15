from utils import *

def generate_chunk_block(k, c):
    data = ''          
    d = "" 
    for x in range(0, 4096):
        d += bin(k)[2:].zfill(9) + bin(c)[2:].zfill(4)
    d = [int(s) for s in d]
    nd = []

    #print(d)
    for i in range(0, len(d), 64):
        out = 0
        for bit in d[i:i+64]:
            out = (out << 1) | bit 
        if i == 0:
            print(d[i:i+64])
            print(bin(out))
        nd.append(struct.pack(">q", (out % 2**64) - 2**64 if (out % 2**64)>=2**(63) else (out % 2**64)))
    #print(nd)
    light = [b'\xff' for i in range(0, 2048)]
    return b'\x0d' + pack_varint(0) + pack_varint(len(nd)) + b''.join(nd[::-1]) +  b''.join(light)


class Player:
    def __init__(self, worker, x, y, grounded, z, yaw, pitch, just_spawned = 1, did_move = 1, did_pitchyaw = 1, running=1, doneupdatespeed = 1, onground = 1, active = 1):
        self.x = x
        self.y = y
        self.grounded = grounded
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
        
        self.need_to_keep_alive = 0
        self.alivecounter = 0

        self.tickcounter = 0

    def tick(self):
        self.tickcounter += 1
        self.tick_since_update = 0
        if self.need_to_respawn:
            self.x = 0
            self.y = 16*2
            self.z = 0
            self.send_pos(self.x, self.y, self.z)
            self.send_chunk()
            self.need_to_respawn = False
        if self.need_to_keep_alive and self.tickcounter > 150:
            self.send_keepalive()
            self.tickcounter = 0

    def send_pos(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z 
        self.worker.send_data(b'\x2e', double(self.x), double(self.y), double(self.z), float(self.yaw), float(self.pitch), b'\x07', pack_varint(0))
        print("sending pos")  

    def send_chunk(self):
        for i in range(0,4):
            print("sending chunk")
            data = generate_chunk_block(2, 0) + generate_chunk_block(0, 0) #grassblocks / air above
            self.worker.send_data(b'\x20', struct.pack('>i',i) , struct.pack('>i',i), b'\x01', pack_varint(18), pack_varint(len(data)), data, pack_varint(0))
            self.send_pos(0, 32, 0)
        self.need_to_keep_alive = 1

    def send_keepalive(self):
        self.alivecounter += 1
        self.worker.send_data(b'\x1f', pack_varint(self.alivecounter))
        #print("sending keepalive")
        if self.alivecounter > 25:
            self.alivecounter = 0
