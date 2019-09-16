import time
import asyncio


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


if __name__ == '__main__':
    ts = TestAsync()
    ts.start()