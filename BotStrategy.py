from datetime import datetime
from RestAccount import RestAccount


class BotStrategy:
    @classmethod
    def model_pred_onemin(cls, prediction, pt_ratio, lc_ratio, ac:RestAccount, amount, ltp):
        ds = BotStateData()
        position = ac.get_position()
        order_side, order_price, order_size, order_dt = ac.get_orders()
        lc_price = int(round(position['price'] * (1.0 - lc_ratio))) if position['side'] == 'Buy' else int(round(position['price'] * (1.0 + lc_ratio)))
        if (position['side'] == 'Buy' and ltp <= lc_price) or (position['side'] == 'Sell' and ltp >= lc_price):
            ds.set_state(False,'', 0, '', 0, 0, 'LC') #do losscut
        elif prediction == 'Buy' or prediction == 'Sell': #prediction通りのposi_sideにしてpt orderを出す
            ds.set_state(False, prediction, amount, 'Buy' if prediction == 'Sell' else 'Sell', 0, 0, 'PT')
        elif (prediction != 'Buy' and prediction != 'Sell') and (position['side'] != prediction):
            ds.set_state(True,'',0,'',0,0,'') #for zero three
        else:
            ds.set_state(True,'',0,'',0,0,'')
        return ds


class BotStateData:
    def __init__(self):
        self.flg_noaction = True
        self.posi_side = ''
        self.posi_size = 0
        self.order_side = ''
        self.order_price = 0
        self.order_size = 0
        self.order_type = '' #Limit, Market, PT, LC

    def set_state(self, flg_noaction, posi_side, posi_size, order_side, order_price, order_size, order_type):
        self.flg_noaction = flg_noaction
        self.posi_side = posi_side
        self.posi_size = posi_size
        self.order_side = order_side
        self.order_price = order_price
        self.order_size = order_size
        self.order_type = order_type


if __name__ == '__main__':
    ds = BotStateData()