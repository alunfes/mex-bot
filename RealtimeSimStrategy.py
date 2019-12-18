from RealtimeSimAccount import RealtimeSimAccount


class RealtimeSimStrategy:
    @classmethod
    def model_prediction_onemin(cls, pred, ac, ltp):
        dd = DecisionData()
        if ac.holding_side != pred:
            if ac.holding_side == '' and (pred == 'Buy' or pred == 'Sell'):  # no position no order
                dd.set_decision(pred, 0, cls.__calc_opt_size(ltp, ac),'Market', False, 10)
            elif (ac.holding_side == 'Buy' or ac.holding_side == 'Sell') and (pred == 'Buy' or pred == 'Sell') and ac.holding_side != pred:
                dd.set_decision(pred, 0,ac.holding_size + cls.__calc_opt_size(ltp, ac),'market', False, 10)  # exit and re-entry
        return dd


    @classmethod
    def __calc_opt_size(cls, price, ac):
        return 0.01


#        return round((ac.asset * ac.leverage) / (price * 1.0 * ac.base_margin_rate), 2)

class DecisionData:
    def __init__(self):
        self.side = ''
        self.size = 0
        self.price = 0
        self.type = 0
        self.cancel = False
        self.expire = 0  # sec

    def set_decision(self, side, price, size, type, cancel, expire):
        self.side = side
        self.price = price
        self.size = size
        self.type = type
        self.cancel = cancel
        self.expire = expire