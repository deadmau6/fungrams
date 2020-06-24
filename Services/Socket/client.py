from mysocket import MySocket
import socket

class Client(MySocket):
    """docstring for Client"""
    def __init__(self):
        super().__init__()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        print(f'Connecting to {self.host}:{self.port}')
        self.client_socket.connect((self.host, self.port))

    def send_data(self, msg):
        packets = self.prepare_msg(msg)
        for p in packets:
            sent = self.client_socket.send(p)
            if sent == 0:
                raise RuntimeError("Socket connection closed")
        print(f'[CLIENT] {len(packets)} Packets sent.')

    def recieve_data(self):
        chunk_num = 1
        reply = ""
        while chunk_num > 0:
            try:
                chunk = self.client_socket.recv(min(self.packet_size, 4096))
                if not chunk: break
                mg_size, chunk_num, msg = self.parse_data(chunk)
            except Exception as e:
                raise e
            else:
                print(f'[CLIENT] Packet recieved - size: {mg_size}, chunk number: {chunk_num}')
                reply += msg

        return reply

    def end(self):
        print('Closing client...')
        self.client_socket.close()

if __name__ == '__main__':
    import time, sys
    client = Client()
    try:
        client.connect()
        client.send_data("hello there jimbo")
        print(client.recieve_data())
    except Exception as e:
        print(f'Client Error: {e}')
        raise e
    finally:
        client.end()
