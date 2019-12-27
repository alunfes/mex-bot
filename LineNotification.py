import requests
import asyncio
import numpy as np
import matplotlib as plt
from LogMaster import LogMaster

class LineNotification:
    @classmethod
    def initialize(cls):
        cls.__read_keys()
        cls.last_error = ''
        cls.line_api = "https://notify-api.line.me/api/notify"
        cls.headers = {"Authorization": "Bearer " + cls.token}
        print('initialized LineNotification')

    @classmethod
    def __read_keys(cls):
        file = open('./ignore/line.txt', 'r')  # 読み込みモードでオープン
        cls.token = file.readline().split(':')[1]
        file.close()

    @classmethod
    def send_performance_notification(cls):
        #loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cls.__send_performance_data())
        # loop.run_until_complete(cls.__send_position_and_order_data())


    @classmethod
    def send_free_message(cls, message):
        #loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cls.__send_free_data(str(message)))


    @classmethod
    def send_error(cls, message):
        #loop = asyncio.new_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cls.__send_error(str(message)))


    @classmethod
    async def __send_error(cls, message):
        if len(message) > 0:
            await cls.__send_message('\r\n' + '[Error]' + '\r\n' +str(message))


    @classmethod
    async def __send_performance_data(cls):
        p = LogMaster.get_latest_performance()
        pred = LogMaster.get_latest_position()
        posi = LogMaster.get_latest_position()
        if len(p) > 0:
            await cls.__send_message('\r\n' + '[' + str(p['dt'].strftime("%m/%d %H:%M:%S")) + ']' +
                                     '\r\n' + 'p:' + str(p['pnl']) + ', p-min:' + str(p['total_pnl_per_min']) +
                                     ', num:' + str(p['num_trade']) + ', rate:' + str(p['win_rate']) +
                                     '\r\n' + str(posi['posi_side']) + ' : ' + str(pred['prediction']))

    @classmethod
    async def __send_free_data(cls, message):
        await cls.__send_message(str(message))



    @classmethod
    async def __send_message(cls, message):
        payload = {"message": message}
        try:
            res = requests.post(cls.line_api, headers=cls.headers, data=payload, timeout=(6.0))
        except Exception as e:
            print('Line notify error!={}'.format(e))

    @classmethod
    async def __send_image(cls, img):
        res = requests.post(cls.line_api, headers=cls.headers, files=img, timeout=(6.0))


if __name__ == '__main__':
    LineNotification.initialize()
    LineNotification.send_error('Total API access reached 500/sec! sleep for 60sec')
    # LineNotification.send_message('\r\n'+'pl=-59'+'\r\n'+'num_trade=100')