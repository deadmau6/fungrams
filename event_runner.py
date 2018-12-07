from EventBus import Manager
import time

if __name__ == '__main__':
    manager = Manager()
    manager.watch_zk()