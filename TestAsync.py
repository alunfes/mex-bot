import time
import asyncio
import threading

class ws:
    def __init__(self):
        self.data = []

    async def add_data(self, d):
        self.data.append(d)
        await asyncio.sleep(1)
        print('num data=',len(self.data))


    def get_data_loop(self):
        loop = asyncio.get_event_loop()
        #queue = asyncio.Queue()
        for i in range(100):
            task = loop.create_task(self.add_data(i))
            loop.run_until_complete(task)
        loop.stop()
        loop.close()


class other_task:
    def task_loop(self):
        for i in range(100):
            print('other task-' + str(i))
            time.sleep(0.5)

class TestAsync:
    def start(self):
        wsin = ws()
        wsin.get_data_loop()
        ot = other_task()
        ot.task_loop()



class thread1:
    @classmethod
    def initialize(cls):
        cls.data = 0
        cls.lock = threading.Lock()

    @classmethod
    def set_data(cls, d):
        with cls.lock:
            cls.data = d

    @classmethod
    def get_data(cls):
        with cls.lock:
            return cls.data


class Update1:
    def thread1(self):
        while True:
            thread1.set_data(1)
            print('th1-', thread1.get_data())
            time.sleep(0.1)

class Update2:
    def thread2(self):
        while True:
            thread1.set_data(2)
            print('th2-', thread1.get_data())
            time.sleep(3)



if __name__ == '__main__':
    thread1.initialize()
    u1 = Update1()
    u2 = Update2()
    th = threading.Thread(target=u1.thread1)
    th.start()
    th2 = threading.Thread(target=u2.thread2)
    th2.start()

    while True:
        time.sleep(1)


