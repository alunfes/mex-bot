from Trade import Trade
from OneMinMarketData import OneMinMarketData
from PrivateWS import PrivateWS, PrivateWSData
from Account import Account
from SystemFlg import SystemFlg
from LgbModel import LgbModel
import threading
from RealtimeWSAPI import TickData
import pytz
import time
import datetime
import pickle


'''
initialize class
load model
start ws
download ohlc
calc all index
downlod ohlc for latest (after last donwload till completion of calc, maybe few minutes data)
calc index only for last downloaded data
predict bpsp

'''

#ohlc data
'''
最初はその時点のutまで普通にapiでohlc dataを最低必要なデータ数ダウンロード(数秒かかる）
その後index計算（数秒かかる）
bot稼働中のohlcはws経由で取得
・最初のohlc取得計算後にbot稼働する際のohlcは1分データ以上の間隔が開く可能性がある。
->
'''


class Bot:
    def __init__(self):
        self.ac = Account()
        self.lgb_model = LgbModel()
        pws = PrivateWS(self.ac)
        Trade.initialize()
        self.amount = 10000

        th = threading.Thread(target=self.__bot_thread)
        th.start()


    def __bot_thread(self):
        next_min = datetime.now().minute +1 if datetime.now().minute +1 < 60 else 0
        flg = False
        while SystemFlg.get_system_flg():
            pred = self.lgb_model.get_pred()
            if (pred == 'Buy' or pred == 'Sell') and pred != self.ac.get_position()['side']:
                res = Trade.order(pred, TickData.get_ask(), 'market', self.amount if self.ac.get_position()['side'] == '' else self.amount + self.ac.get_position()['size'])
                if 'info' in res:
                    self.ac.add_order(res['info']['orderID'], pred, 0, self.amount, 'New')
                else:
                    print('Trade Order Response is invalid!')
                    print(res)

            if datetime.now().minute == next_min and flg:
                next_min = next_min + 1 if next_min + 1 < 60 else 0
                flg = False
            if 
            time.sleep(0.3)





    def combine_status_data(self, status):
        side = ''
        size = 0
        price = 0
        for s in status:
            side = s['side'].lower()
            size += float(s['size'])
            price += float(s['price']) * float(s['size'])
        price = round(price / size)
        return side, round(size, 8), round(price)

    def sync_position_order(self):
        position = Trade.get_positions()
        orders = Trade.get_orders()
        if len(position) > 0:
            posi_side, posi_size, posi_price = self.combine_status_data(position)
            if self.posi_side != posi_side or self.posi_price != posi_price or self.posi_size != posi_size:
                print('position unmatch was detected! Synchronize with account position data.')
                print('posi_side={},posi_price={},posi_size={}'.format(self.posi_side, self.posi_price, self.posi_size))
                print(position)
            self.posi_side, self.posi_size, self.posi_price = posi_side, posi_size, posi_price
            self.posi_status = 'fully executed'
            print('synchronized position data, side=' + str(self.posi_side) + ', size=' + str(
                self.posi_size) + ', price=' + str(self.posi_price))
        else:
            self.posi_initialzie()
        if len(orders) > 0:  # need to update order status
            if len(orders) > 1:
                print('multiple orders are found! Only the first one will be synchronized!')
            self.order_id = orders[0]['info']['child_order_acceptance_id']
            self.order_side = orders[0]['info']['side'].lower()
            self.order_size = float(orders[0]['info']['size'])
            self.order_price = round(float(orders[0]['info']['price']))
            print('synchronized order data, side=' + str(self.order_side) + ', size=' + str(
                self.order_size) + ', price=' + str(self.order_price))
        else:
            self.order_initailize()



if __name__ == '__main__':
    bot = Bot()
    bot.initialize()
    df = OneMinMarketData.generate_df_from_dict()
    df.to_csv('./Data/df.csv')