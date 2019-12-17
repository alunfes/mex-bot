import random
from datetime import datetime
from Trade import Trade
from RealtimeWSAPI import TickData


class BotStrategy:
    @classmethod
    def sim_model_pred_onemin(cls, prediction, pt_ratio, lc_ratio, ac, amount):
        dd = DecisionData()
        if TickData.get_ask() > 0:
            position = ac.get_position()
            order_side, order_price, order_size, order_dt = ac.get_orders()
            pt_price = int(round(position['price'] * (1.0 + pt_ratio))) if position['side'] == 'Buy' else int(round(position['price'] * (1.0 - pt_ratio)))
            if position['side'] != prediction:
                if position['side'] == '' and (prediction == 'Buy' or prediction == 'Sell'):  # no position no order
                    dd.set_decision(prediction, 0, amount, 'Market', False) #entry order
                elif (position['side'] == 'Buy' or position['side'] == 'Sell') and (prediction == 'Buy' or prediction == 'Sell') and position['side'] != prediction and len(order_side) > 0:
                    dd.set_decision('', 0, 0, '', True) #cancel pt order before exit and re-entry
                elif (position['side'] == 'Buy' or position['side'] == 'Sell') and (prediction == 'Buy' or prediction == 'Sell') and position['side'] != prediction and len(order_side) == 0:
                    dd.set_decision(prediction, 0, position['size'] + amount, 'Market', False)  # exit and re-entry
                elif position['side'] != '' and len(order_side) == 0:
                    dd.set_decision('Buy' if position['side'] == 'Sell' else 'Sell', pt_price, position['size'], 'Limit', False) #place a pt limit order
                elif position['side'] != '' and position['price']

        return dd

    @classmethod
    def sim_model_pred_onemin_avert(cls, prediction, pt_ratio, lc_ratio, ac, ac2, avert_period_kijun, avert_val_kijun, amount):



    '''
    randomな方向にエントリーして、pt = 10の指値を入れる。
    entry limit orderが1分経過してもFilledにならなければ残りをキャンセル。
    10分経過してもptしなければexit order出す。
    '''
    @classmethod
    def random_pl_taker(cls, ac, amount):
        dd = DecisionData()
        if TickData.get_ask() > 0:
            position = ac.get_position()
            order_side, order_price, order_size, order_dt = ac.get_orders()
            order_ids = list(order_side.keys())

            if len(order_ids) > 1:
                print('multiple order found error!')
                for key in order_side.keys():
                    Trade.cancel_order(key)
            else:
                if position['side'] == '' and len(order_side) == 0:
                    side = 'Buy' if random.randint(0,1) == 0 else 'Sell'
                    dd.set_decision(side, TickData.get_ask() if side == 'Buy' else TickData.get_ask(), amount, 'Limit', False)
                elif position['side'] == '' and len(order_side) == 1: #when no holding position and order exist
                    if (datetime.now() - order_dt[order_ids[0]]).seconds > 60: #cancel order
                        dd.set_decision('', 0, 0, '', True)
                elif position['side'] != '' and len(order_side) == 0 and (datetime.now() - position['dt']).seconds < 600: #when holding position but no order exist
                    dd.set_decision('Buy' if position['side'] == 'Sell' else 'Sell', position['price'] + 10, position['size'], 'Limit', False) #pt order
                elif position['side'] != '':
                    if (datetime.now() - position['dt']).seconds > 600:
                        side = 'Buy' if position['side'] == 'Sell' else 'Sell'
                        if len(order_side) > 0:
                            dd.set_decision('', 0, 0, '', True)
                        else:
                            dd.set_decision(side, TickData.get_ask() if side == 'Buy' else TickData.get_ask(), position['size'], 'Limit', False)  #exit when 10 min passed. exit orderが一部だけ約定して想定外の動きになることがありうる
                else:
                    print('Unknown situation!')
                    print('holding:', position['side'], ac.get_position()['price'], ac.get_position()['size'])
                    for order in order_side:
                        print(order_side[order], order_price[order], order_size[order], order_dt[order])
        return dd


class DecisionData:
    def __init__(self):
        self.side = ''
        self.size = 0
        self.price = 0
        self.type = 0
        self.cancel = False

    def set_decision(self, side, price, size, type, cancel):
        self.side = side
        self.price = price
        self.size = size
        self.type = type
        self.cancel = cancel


if __name__ == '__main__':
    dd = DecisionData()
    print(dd.side)