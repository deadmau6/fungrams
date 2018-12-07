from multiprocessing import Process
import select, random, time

class EventBase(Process):
    """The EventBase class

    This class is a parent class as for the event types.
    Therefore this class should only be inherited!
    This class holds the basic communication with the manager.
    """

    def __init__(self, event_pipe):
        Process.__init__(self)
        # Pipe/Connection for writing updates TO the manager.
        self.event_pipe = event_pipe
        

    def report(self, status_report):
        """Send an update to the manager."""
        self.event_pipe.send(status_report)

    def finish(self, conclusion='END'):
        """Conclusion message to the manager."""
        self.event_pipe.send(conclusion)
        self.event_pipe.close()

    def run(self):
        res_code = random.randrange(100, 999)
        elapse_time = 1
        for i in range(3):
            if self.event_pipe.poll(1):
                self.report("Canceling....")
                break
            color = random.choice(['blue', 'red', 'yellow', 'green', 'violet'])
            time.sleep(elapse_time)
            self.report({'id': res_code, 'etime': elapse_time, 'color': color, 'round': i})
        self.finish()

