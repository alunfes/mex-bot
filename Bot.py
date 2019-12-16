from Trade import Trade
from OneMinMarketData import OneMinMarketData
from PrivateWS import PrivateWS, PrivateWSData
from Account import Account
from SystemFlg import SystemFlg
from LgbModel import LgbModel
from BotStrategy import BotStrategy, DecisionData
from LineNotification import LineNotification
from LogMaster import LogMaster
import threading
from RealtimeWSAPI import TickData
import pytz
import time
from datetime import datetime
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


戦略は複雑で、2つのACを使うものや複数モデルの運用により意思決定するものがあるため、
Botでは戦略意思決定、トレード、口座、Line, Logなどの管理を役割とする。
'''



class Bot:
    def __init__(self):
        pws = PrivateWS()
        Trade.initialize()
        self.ac = Account()
        self.omd = OneMinMarketData
        #self.lgb_model = LgbModel()
        LineNotification.initialize()
        self.amount = 10
        th = threading.Thread(target=self.__bot_thread)
        th2 = threading.Thread(target=self.__bot_sub_thread)
        th.start()
        th2.start()


    def __bot_thread(self):
        next_min = datetime.now().minute +1 if datetime.now().minute +1 < 60 else 0
        flg = False
        while SystemFlg.get_system_flg():
            #pred = self.lgb_model.get_pred()
            #dd = BotStrategy.model_prediction_onemin(pred, self.ac, self.amount)
            dd = BotStrategy.random_pl_taker(self.ac, self.amount)
            if dd.cancel:
                oid = self.ac.get_order_ids()[0]
                print('bot cancel order', oid)
                cancel = Trade.cancel_order(oid) #accountでcancelを補足して処理する前にbotで再度cancelしてしまう。
                print('cancel res', cancel)
                self.ac.bot_cancel_order(oid)
            else:
                if (dd.side == 'Buy' or dd.side == 'Sell'):
                    res = Trade.order(dd.side, dd.price, dd.type, dd.size)
                    if 'info' in res:
                        self.ac.add_order(res['info']['orderID'], dd.side, dd.price, dd.size, dd.type)
                    else:
                        print('Trade Order Response is invalid!', res)

    def __bot_sub_thread(self):
        while SystemFlg.get_system_flg():
            time.sleep(60)
            print(datetime.now())
            print(self.ac.get_position())
            order_side, order_price, order_size, order_dt = self.ac.get_orders()
            for o in order_side:
                print('order ', o, ', side=', order_side[o], ', price=', order_price[o], ', size=', order_size[o])
            print(self.ac.get_performance())

            posi_side, posi_price, posi_size, posi_dt = self.ac.get_position()
            order_side, order_price, order_size, order_dt = self.ac.get_orders()
            order_sides, order_prices, order_sizes, order_dts = ''
            for oid in order_side:
                order_sides = order_sides + ' : ' + order_side[oid]
                order_prices = order_prices + ' : ' + order_price[oid]
                order_sizes = order_sizes + ' : ' + order_size[oid]
                order_dts = order_dts + ' : ' + order_dt[oid]
            performance = self.ac.get_performance() #{'total_pl':self.realized_pnl + self.unrealized_pnl + self.total_fee, 'num_trade':self.num_trade, 'win_rate':self.win_rate, 'total_fee':self.total_fee}
            LogMaster.add_log({'log_dt':datetime.now(), 'dt':self.omd.ohlc.dt[-1], 'open':self.omd.ohlc.open[-1], 'high':self.omd.ohlc.high[-1],
                               'low':self.omd.ohlc.low[-1], 'close':self.omd.ohlc.close[-1], 'posi_side':posi_side, 'posi_price':posi_price, 'posi_size':posi_size,
                               'order_side':order_sides,'order_price':order_prices, 'order_size':order_sizes, 'num_private_access':Trade.num_private_access,
                               'num_public_access':Trade.num_public_access, 'pnl':performance['total_pnl'], 'pnl_per_min':performance['total_pnl_per_min'],
                               'num_trade':performance['num_trade'], 'win_rate':performance['win_rate'], 'prediction':LgbModel.get_pred(), 'api_error':'', 'action_message':'Move to next'})
            LineNotification.send_performance_notification()





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