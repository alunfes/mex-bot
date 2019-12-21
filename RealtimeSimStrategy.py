from RealtimeSimAccount import RealtimeSimAccount


class RealtimeSimStrategy:
    @classmethod
    def model_prediction_onemin(cls, prediction, lc_ratio, amount, ac:RealtimeSimAccount, ltp):
        ds = StateData()
        lc_price = int(round(ac.holding_price * (1.0 - lc_ratio))) if ac.holding_side == 'Buy' else int(round(ac.holding_price * (1.0 + lc_ratio)))
        if (ac.holding_side == 'Buy' and ltp <= lc_price) or (ac.holding_side == 'Sell' and ltp >= lc_price):
            ds.set_state(False, '', 0, '', 0, 0, 'LC')  # do losscut
        elif prediction == 'Buy' or prediction == 'Sell':  # prediction通りのposi_sideにしてpt orderを出す
            ds.set_state(False, prediction, amount, 'Buy' if prediction == 'Sell' else 'Sell', 0, 0, 'PT')
        elif (prediction != 'Buy' and prediction != 'Sell') and (ac.holding_side != prediction):
            ds.set_state(True, '', 0, '', 0, 0, '')  # for zero three
        else:
            ds.set_state(True, '', 0, '', 0, 0, '')
        return ds


    @classmethod
    def __calc_opt_size(cls, price, ac):
        return 0.01


class StateData:
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