import struct

d = ""
for x in range(0, 4096):
    d += bin(2)[2:].zfill(9) + bin(0 & 0x0F)[2:].zfill(4)
d = [int(s) for s in d]
print(d)
nd = []
for i in range(0, len(d), 64):
        out = 0
        for bit in d[i:i+64]:
            out = (out << 1) | bit

        nd.append(struct.pack(">Q", out))
        
print(nd)
print(len(nd))
