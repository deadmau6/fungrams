from Socket import MySocket
import time

def test_packet_conversion(message="Hi", packet_size=16):
    m_sock = MySocket(packet_size=packet_size)
    packets = m_sock.prepare_msg(message)
    chunk_num = 1
    index = 0
    reply = ''
    while chunk_num > 0:
        try:
            mg_size, chunk_num, msg = m_sock.parse_data(packets[index])
        except Exception as e:
            print(f'Error : {index} , {e}')
            break
        else:
            print(f'Packet size: {mg_size}, Chunk Number: {chunk_num}, Message: {msg}')
            reply += msg
            index += 1
    print(reply)

if __name__ == '__main__':
    print('"Ctrl-C" to end the process:')
    while True:
        try:
            usr_msg = input('--> ')
        except KeyboardInterrupt:
            print('\nExiting...')
            break
        else:
            test_packet_conversion(message=usr_msg)
            time.sleep(0.5)

