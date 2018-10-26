import random

class Station:

    def __init__(self):
        self.names = ['Olivia', 'Emma', 'Ava','Charlotte', 'Mia', 'Sophia','Isabella','Harper','Amelia','Evelyn','Noah','Liam','Benjamin','Oliver','William','James','Elijah','Lucas','Mason','Michael']

    def generate_arrival(self, limit=None):
        line = []
        if limit:
            for i in range(limit):
                name = random.choice(self.names)
                line.append(self.generate_passenger(name))
        else:
            for name in self.names:
                line.append(self.generate_passenger(name))
        return line

    def generate_passenger(self, name):
        sx = random.choice(['M', 'F'])
        age = random.randrange(19, 55)
        bus = random.choice(['blue', 'red', 'yellow'])
        return {
            'name':name,
            'sex':sx,
            'age':age,
            'bus':bus
        }

    def _worker_queue(in_que, out_que):
        for task in iter(in_que.get, 'END'):
            results = task.handle()
            out_que.put(results)

    def _worker_pipe(conn, tasks):
        for task in tasks:
            results = task.handle()
            conn.send(results)
        conn.send('END')
        conn.close()