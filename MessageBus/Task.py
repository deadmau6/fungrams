import time

class Task:

    def __init__(self, passenger):
        self.priority = 0
        self.id = None
        self.name = passenger['name']
        self.sex = passenger['sex']
        self.age = passenger['age']
        self.bus_type = passenger['bus']

    def handle(self):
        if self.bus_type == 'blue':
            return self.blue_bus()
        elif self.bus_type == 'red':
            return self.red_bus()
        else:
            return self.yellow_bus()

    def blue_bus(self):
        self.priority = 1
        self.id = f'#BLUE:{self.name}{self.age}{self.sex}'
        return self.toObject()

    def red_bus(self):
        self.priority = 2
        self.id = f'#RED:{self.name}{self.age}{self.sex}'
        return self.toObject()

    def yellow_bus(self):
        self.priority = 3
        self.id = f'#YELLOW:{self.name}{self.age}{self.sex}'
        return self.toObject()

    def toObject(self):
        #time.sleep(self.priority)
        return {
            'priority': self.priority,
            'id': self.id,
            'name': self.name,
            'sex': self.sex,
            'age': self.age,
            'bus': self.bus_type
        }

