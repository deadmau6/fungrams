from mysocket import MySocket
import socket

class Server(MySocket):

    def __init__(self):
        super().__init__()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, listen=5):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(listen)
        print(f'Listening on {self.host}:{self.port}')
        client, addr = self.server_socket.accept()
        print(f'Connected with {addr[0]}')
        with client:
            chunk_num = 1
            reply = ''
            while chunk_num > 0:
                try:
                    chunk = client.recv(min(self.packet_size, 4096))
                    if not chunk: break
                    mg_size, chunk_num, msg = self.parse_data(chunk)
                except Exception as e:
                    print(f'Server-Client Error: {e}')
                    raise e
                else:
                    reply += msg.replace(' ', '_')
                    print(f'[SERVER] Packet recieved - size: {mg_size}, chunk number: {chunk_num}')

            # Now send the data.
            packets = self.prepare_msg(reply)
            for p in packets:
                client.send(p)
            print(f'[SERVER] {len(packets)} Packets sent.')
    
    def end(self):
        print('Closing server...')
        self.server_socket.close()

if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except Exception as e:
        print(f'Server Error: {e}')
        raise e
    finally:
        server.end()
