#!/usr/bin/python3
import socket
import struct
import json
import time
import threading

DEBUG = True
SHOW_TICKS = True
MAX_PLAYERS = 10

#custom modules
import player
from player import Player

from utils import *
players = []

class Server:
    def __init__(self, host='localhost', port=25565, timeout=5, state = 0):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._threads = []

    
    def host(self):
        with socket.socket(socket.SO_REUSEADDR) as s:
            s.bind((self._host, self._port))
            s.listen(10)
            print("Server started on " + self._host + ":" + str(self._port))
            tick_thread = threading.Thread(target = self.tick, args=())
            tick_thread.start()
            while 1:
                conn, addr = s.accept()
                print("Accepted connection from " + addr[0] + ":" + str(addr[1]))
                worker = Worker(self, conn, str(addr[0])+str(addr[1]))
                t = threading.Thread(target = worker.start, args = ())
                self._threads.append(t)
                t.start()
            s.close()
        print("Server stopped!")
    
    def tick(self):
        while 1:
            time.sleep(0.05)
            for player in players:
                player.tick()
                #if SHOW_TICKS:
                #    print(player.username)

class Worker:
    def __init__(self, server, conn, id, state=0):        
        self._server = server
        self._state = state
        self._id = id
        self._buffer = b''
        self._cursor = 0
        self._conn = conn
        self._packet_length = 0        
        
        self.username = "Undefined :P"
        
        self._break = 0
        self._player = ''
   
    def read_byte(self, c=1):
        self._cursor += c
        if (self._cursor < self._packet_length + 1):
            return self._buffer[self._cursor - c:self._cursor]
        return b''
    
    def read_varint(self): 
        data = 0
        for i in range(5):
            ordinal = self.read_byte()
            if len(ordinal) == 0:
                break
            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7*i
            if not byte & 0x80:
                break
        return data
    
    def read_string(self):
        len = self.read_varint()
        return self.read_byte(len)

    def recv(self):
        self._cursor = 0
        self._packet_length = unpack_varint(self._conn)
        self._buffer = self._conn.recv(self._packet_length)
        return self.read_varint()

    def send_data(self,  *args):
        data = b''

        for arg in args:
            data += pack_data(arg)
        print(len(data))
        self._conn.send(pack_varint(len(data)) + data)
    
    def handle(self):
        #(packet_id, prot, string, packet_length, data, port) = self._read_fully(conn,  True)
        #print(str(packet_id) + " : " + str(data))
        #print("packetid: " + str(packet_id))
        #print("prot: " + str(prot))
        #print("str: " + string.decode("utf-8"))
        #print("state: " + str(state))
        #print("port: %s" % struct.unpack('>H', port))
        
        packet_id = self.recv()

        if DEBUG:
            print("id: %s" % packet_id)
            print("state: %s" % self._state)
            print("buffer: %s" % self._buffer)
            print("count: %s" % self._cursor)
            print("length: %s" % self._packet_length)
        
        if self._state == 0:
            if packet_id == 0x00:
                prot = self.read_varint()
                addr = self.read_string()
                port = self.read_byte(2)
                self._state = self.read_varint()
                if DEBUG:
                    print("handshaking")
                    print("str: %s" % addr.decode("utf-8"))
                    print("port: %s" % port)
                    print("Switched to state: %s" % self._state)
        elif self._state == 1:
            if packet_id == 0x00: 
                self.send_data(b'\x00', 
                    """{
                     
                    "version": {
                         "name": "1.11.2",
                         "protocol": 316
                     },
                    "players": {
                     "max": """ + str(MAX_PLAYERS) + """,
                     "online": 0
                    },
                    "description": {   
                      "text": "Hello world"
                     }
                    } """.replace("\n", ""))
                if DEBUG:
                    print("sending status")
            elif packet_id == 0x01:
                payload = self.read_byte(8)
                self.send_data(b'\x01', payload)
                if DEBUG:
                    print("pinging")
        elif self._state == 2:
            if packet_id == 0x00:
                self.username = self.read_string().decode("utf-8")
                print("%s is logging in..." % self.username)
                self.login()
        elif self._state == 3:
            print("state 3")
            if packet_id == 0x04:
                print("client settings received")
            elif packet_id == 0x09:
                channel = self.read_string().decode("utf-8")
                print("p-channel: %s" % channel)
            elif packet_id == 0x0b:
                id = self.read_varint()
                self.send_data(b'\x0b', pack_varint(id))
                print("keeping alive") 
        #input("press a key") 
    
    def login(self):
        self.send_data(b'\x02', "4a1d6813-c6aa-40b2-ab97-d3d5aa4561d0", self.username) #login success
        self._state = 3
        print("login")
        #EID, gamemode, dimension, diff, max players, level type (default), debug info
        self.send_data(b'\x23', struct.pack("i",1337), b'\x01', struct.pack("i",0), b'\x01', b'\x00', "default", b'\x00') #spawn player
        player = Player(self, 0, 0, 0, 0, 0, 0)
        player.need_to_respawn = True        
        players.append(player)

    def start(self):
        while self._break == 0:
            try:
                self.handle()
            except socket.error:
                self._conn.close()
                print("closed connection with: %s" % self._id)
                break
            except:
                print("A general error occured")
                print("Unexpected error:", sys.exc_info()[0])
                raise
                

server = Server()
server.host()
