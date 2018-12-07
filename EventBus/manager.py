#from .connections import Zookeeper
from multiprocessing import Process, Pipe, Queue, freeze_support
from .event_base import EventBase
import select

class Manager:
    """The Manager class

    This class is an event driven process manager.
    It should handle/update requests from Zookeeper.
    It also manages/dispatches different savant processes (ie searcher, or even the api).
    """

    def __init__(self):
        self.processes = {}
        # Holds the total active events by id.
        self.active_events = {}
        # Holds the event connection for each dispatch pipe.
        self.active_pipes = {}
        self.event_pipes = []
        self.dispatch_pipes = []
        self.broken_pipes = []

    def handle_request(self, request_obj):
        if request_obj == '':
            return
        req = request_obj.split(' ')
        if req[0] == 'stop:':
            self.cancel_event(int(req[1]))
            return
        elif req[0] == 'run:':
            self.start_event(int(req[1]))
            return
        else:
            print('Unknown Command')
            return

    def handle_update(self, pipe_fileno, update_obj):
        if update_obj == 'END':
            print("Finished.")
            self.close_event(pipe_fileno)
        else:
            print(update_obj)

    def watch_zk(self):
        while True:
            try:
                readable, writable, errors = select.select(self.dispatch_pipes, self.event_pipes, self.event_pipes,  1)
                if readable:
                    for conn in readable:
                        self.read_event(conn)
                else:
                    user_msg = input() 
                    self.handle_request(user_msg)
            except KeyboardInterrupt:
                print('\nExiting...')
                for pipe_fileno in self.active_pipes.keys():
                    self.close_event(pipe_fileno)
                print('\nComplete!')
                break

    def update_zk(self):
        pass

    def register_event(self, event_id):
        """Adds the event information to the EventBus."""
        parent_conn, child_conn = self.register_pipe()
        self.active_pipes[parent_conn.fileno()] = event_id
        self.active_events[event_id] = (parent_conn, child_conn)
        return parent_conn, child_conn

    def start_event(self, event_id):
        if event_id in self.active_events.keys():
            print('Event already exists')
        else:
            parent_conn, child_conn = self.register_pipe()
            self.active_pipes[parent_conn.fileno()] = event_id
            event = EventBase(child_conn)
            event.start()
            self.active_events[event_id] = (parent_conn, child_conn, event)

    def read_event(self, conn):
        """Reads data sent from the spawned event through its pipe."""
        try:
            update_obj = conn.recv()
        except EOFError as ef:
            print("Cannot Read Event, it must've abruptly close.", ef)
            self.close_pipe(conn.fileno())
        else:
            self.handle_update(conn.fileno(), update_obj)

    def cancel_event(self, event_id, cancel_msg='STOP'):
        """Sends a cancel message to the child event."""
        if event_id in self.active_events.keys():
            parent_conn = self.active_events[event_id][0]
            parent_conn.send(cancel_msg)

    def register_pipe(self):
        """Add a pipe to the EventBus.

        Returns the dispatch's (or parent's) connection object
        and event's (or child's) connection object.
        """
        parent_conn, child_conn = Pipe() 
        self.dispatch_pipes.append(parent_conn)
        self.event_pipes.append(child_conn)
        return parent_conn, child_conn

    def close_event(self, pipe_fileno):
        """Safely closes an event and it's pipes.

        Keyword arguments:
        pipe_fileno -- should be a Connection Object's fileno which acts like a unique id
        """
        try:
            # The active_pipes should return the event id.
            event_id = self.active_pipes.pop(pipe_fileno)
            parent_conn, child_conn, event = self.active_events.pop(event_id)
            self.event_pipes.remove(child_conn)
            self.dispatch_pipes.remove(parent_conn)
        except KeyError as ke:
            print("The active pipe key does not exist.\n", ke)
        except ValueError as ve:
            print("Connection object does not exist.\n", ve)
        finally:
            child_conn.close()
            parent_conn.close()
            event.terminate()
            event.join()
        