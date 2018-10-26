from multiprocessing import Process, Pipe, Queue, freeze_support
from MessageBus import Task, Station
import select

dispatch = []
busses = []
active_pipes = {}

def test_queues(arrival_q, done_q, limit=None):
    station = Station()

    line1 = station.generate_arrival(limit=limit)

    for p in line1:
        arrival_q.put(Task(p))

    
    Process(target=Station._worker_queue, args=(arrival_q, done_q)).start()

def mp_queue_testing(limit=None):
    out_size = limit * 3 if limit else 20 * 3
    arrival_q = Queue()
    done_q = Queue()
    for i in range(3):
        test_queues(arrival_q, done_q, limit=limit)

    for i in range(out_size):
        print('\t', done_q.get())

    for i in range(3):
        arrival_q.put('END')

def read(conn):
    try:
        data = conn.recv()
    except Exception as e:
        conn.close()
    else:
        if data == 'END':
            bus_conn = active_pipes.pop(conn.fileno())
            busses.remove(bus_conn)
            dispatch.remove(conn)
            #bus_conn.close()
            conn.close()
        else:
            print('\t', data)

def test_pipes(limit=None):
    parent_conn, child_conn = Pipe()
    active_pipes[parent_conn.fileno()] = child_conn
    dispatch.append(parent_conn)
    busses.append(child_conn)
    station = Station()

    line1 = station.generate_arrival(limit=limit)

    tasks = [Task(p) for p in line1]

    Process(target=Station._worker_pipe, args=(child_conn, tasks)).start()

def mp_pipe_testing(limit=None):
    
    for i in range(3):
        test_pipes(limit=limit)

if __name__ == '__main__':
    #freeze_support()
    #mp_queue_testing(limit=5)
    #mp_pipe_testing(limit=5)
    while True:
        try:
            readable, writable, errors = select.select(dispatch, busses, busses, 1)
            if not readable:
                usr_msg = input('--> ')
                if not usr_msg == '':
                    mp_pipe_testing(limit=int(usr_msg))
            else:
                for bus in readable:
                    read(bus)
        except KeyboardInterrupt:
            print('\nExiting...')
            print([x.fileno() for x in dispatch])
            print([x.fileno() for x in busses])
            print(active_pipes)
            break

