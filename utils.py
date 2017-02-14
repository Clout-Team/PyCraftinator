import struct



def unpack_varint(sock):
        data = 0
        for i in range(5):
            ordinal = sock.recv(1)
            if len(ordinal) == 0:
                break
            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7*i

            if not byte & 0x80:
                break
        return data

def pack_varint(data):
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack("B", byte | (0x80 if data > 0 else 0))

            if data == 0:
                break
            
        return ordinal
    
def pack_data(data):
        if type(data) is str:
            data = data.encode('utf-8')
            return pack_varint(len(data)) + data
        elif type(data) is int:
            return struct.pack('H', data)
        elif type(data) is float:
            return struct.pack('L', int(data))
        else:
            return data
    
def read_fully(connection, string=False, extra_varint=False):
        """ read conn and return bytes """
        packet_length = unpack_varint(connection)
        packet_id = unpack_varint(connection)
        byte = b''
    
        port = 0
        string = b""
        byte = b''
        port = 1337
        prot = 0

        
        '''
        if False:
            if extra_varint:
                # Packet contained netty header offset for this
                if packet_id > packet_length:
                    self._unpack_varint(connection)

                extra_length = self._unpack_varint(connection)
    
                while len(byte) < extra_length:
                    byte += connection.recv(extra_length)
            else:
                byte = connection.recv(packet_length)
        
            return packet_id, packet_length, byte
        
        elif self._state == 0:
            prot = self._unpack_varint(connection)
            string_length = self._unpack_varint(connection)
            string = b'';
            while len(string) < string_length:
                string += connection.recv(string_length)
                byte += string
        '''

        byte = connection.recv(packet_length)
        
        return packet_id, prot, string,  packet_length, byte, port


def double(i):
    return struct.pack("d", i)

def float(i):
    return struct.pack("f", i)
