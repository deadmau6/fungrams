from EventBus import Manager

if __name__ == '__main__':
    manager = Manager()
    manager.watch_zk()