
class MySocket:

    def __init__(self, host='localhost', port=5001, packet_size=32, msg_flag=4, chunk_flag=4):
        self.host = host
        self.port = port
        self.packet_size = packet_size
        # Size of the header field that specifies the message length.
        self.h_msg_size = msg_flag
        # Size of the header field that specifies the number of chunks.
        self.h_chunknum_size = chunk_flag
        # Size of the header
        self.header_size = self.h_msg_size + self.h_chunknum_size
        # Data size limit - used to determine if data needs to be chunked.
        self.msg_limit = self.packet_size - self.header_size

    def prepare_msg(self, msg):
        msg_size = len(msg)
        if msg_size > self.msg_limit:
            chunks = []
            msg_segments = [msg[x - self.msg_limit : x] for x in range(self.msg_limit, msg_size+self.msg_limit, self.msg_limit)]
            chunk_num = len(msg_segments)
            for seg in msg_segments:
                chunk_num -= 1
                seg_size = str(len(seg))
                data = bytes(seg_size, 'utf-8').zfill(self.h_msg_size)
                data += bytes(str(chunk_num), 'utf-8').zfill(self.h_chunknum_size)
                data += bytes(seg, 'utf-8')
                chunks.append(data)
            return chunks

        # Message does not need to be chunked
        data = bytes(str(msg_size), 'utf-8').zfill(self.h_msg_size)
        data += bytes('0', 'utf-8').zfill(self.h_chunknum_size)
        data += bytes(msg, 'utf-8')
        return [data]

    def parse_data(self, data):
        msg_size = int(data[:self.h_msg_size])
        chunk_num = int(data[self.h_msg_size:self.header_size])
        msg = str(data[self.header_size:], 'utf-8')
        return (msg_size, chunk_num, msg)

