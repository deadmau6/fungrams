from multiprocessing import Process, Pipe
from threading import Thread
from .example_events import YellMessage, ReverseMessage, CompressMessage
import select, json, time
#TODO: Add logging.

class Manager:
    """The Manager class

    This class is an event driven process manager.
    """

    def __init__(self):
        # Holds the total active events by id.
        self.active_events = {}
        # Holds the event connection for each dispatch pipe.
        self.active_pipes = {}
        # The event pipes are a one way connection from event to manager(updating).
        self.event_pipes = []
        # The dispatch pipes are a one way connection from manager to event(cancelling events).
        self.dispatch_pipes = []
        # TODO: boken pipes should contain both pipes and is only used for catching errors.
        self.broken_pipes = []

    def handle_request(self, request_obj):
        """This function accepts a dictionary object.

        The purpose of this function is to parse any necessary portions
        of the request that applies to actions of an event.
        (ie start, pause, or stop an event)
        """
        if request_obj.get('cancel'):
            print(f"Cancel request recieved for {request_obj['id']}")
            self.cancel_event(request_obj['id'])
        else:
            self.start_event(request_obj)

    def handle_update(self, pipe_fileno, update_obj):
        """This function parses the event's update request and can act accordingly.

        It should be noted that this function is intended to be a global interpreter for all events.
        """
        if update_obj.get('status') == 'DONE':
            print(f"{update_obj['name']}:{update_obj['id']}({update_obj['status']}) - {update_obj['update']}")
        else:
            print(f"{update_obj['name']}:{update_obj['id']}({update_obj['status']}) - {update_obj['update']}")

    def monitor(self):
        # def _monitor():
        while True:
            try:
                # This watches the currently active events for updates.
                readable, writable, errors = select.select(
                    self.dispatch_pipes, self.event_pipes, self.event_pipes, 0.001)
                for conn in readable:
                    self.read_event(conn)
            except KeyboardInterrupt:
                print('\nExiting...')
                for pipe_fileno in self.active_pipes.keys():
                    self.close_event(pipe_fileno)
                print('\nComplete!')
                return
            except Exception as e:
                print(f'\nError: {e}')
                print('Exiting...')
                for pipe_fileno in self.active_pipes.keys():
                    self.close_event(pipe_fileno)
                print('\nComplete!')
                return
            time.sleep(0.001)
        # self.monitor_thread = Thread(target=_monitor, name=f"{self.__class__.__name__} manager monitor")
        # self.monitor_thread.setDaemon(True)
        # self.monitor_thread.start()

    def register_event(self, conn, event_obj):
        """Registers a particular event based on the typ.

        Keyword arguments:
        conn -- connection to the manager(required by all events).
        event_obj --  arguments of the event(required by all events).      

        Returns the specified Event Instance (ie Searcher)
        """
        typ = event_obj['type'].lower()
        if typ == 'compress':
            return CompressMessage(conn, event_obj)
        elif typ =='yell':
            return YellMessage(conn, event_obj)
        else:
            return ReverseMessage(conn, event_obj)

    def start_event(self, event_obj):
        """Starts the event."""
        event_id = event_obj['id']
        if event_id in self.active_events.keys():
            # This means that the same request was made twice in a row.
            print("Event already exists!")
        else:
            # Register and get the connection pipes between manager and event.
            parent_conn, child_conn = self.register_pipe()
            # Create an association between the manager pipe and event id.
            self.active_pipes[parent_conn.fileno()] = event_id
            # Get the specific event based on the type field.
            event = self.register_event(child_conn, event_obj)
            # The event needs to subclass Process from python's multiprocessing in order for this to work.
            event.start()
            # Create an association to the event id and all of it's connections/process objects.
            self.active_events[event_id] = (parent_conn, child_conn, event)
            # Log or print out the event created.
            print(f'Event PID: {event.pid}')

    def read_event(self, conn):
        """Reads data sent from the spawned event through its pipe."""
        try:
            update_obj = conn.recv()
        except (EOFError, OSError) as ef:
            print("Cannot Read Event, it must've abruptly close.", ef)
            self.close_pipe(conn.fileno())
        else:
            self.handle_update(conn.fileno(), update_obj)

    def cancel_event(self, event_id):
        """Sends a cancel message to the child event."""
        if event_id in self.active_events:
            parent_conn = self.active_events[event_id][0]
            parent_conn.send('abort')

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

        In case the data comes back unreadable or just wrong we want to close the event at
        all cost. The pipe_fileno is the only guarentee for both broken and working pipes.
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
            # Close the connections.
            child_conn.close()
            parent_conn.close()
            # Kill the event, otherwise it will act a 'defunct' or a zombie on the OS.
            event.terminate()
            # Ensure that the event has terminated.
            event.join()
        