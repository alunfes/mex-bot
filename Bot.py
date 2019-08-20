from Trade import  Trade
import pytz
import time
from numba import jit


class Bot:
    @jit
    def initialize(self, pl_kijun):
        self.pl_kijun = pl_kijun
        self.posi_initialzie()
        self.order_initailize()
        self.initial_collateral = Trade.get_collateral()['btc']['free']
        self.collateral_change = 0
        self.pl = 0
        self.holding_pl = 0
        self.pl_log = []
        self.num_trade = 0
        self.num_win = 0
        self.win_rate = 0
        self.pl_per_min = 0
        self.elapsed_time = 0
        self.margin_rate = 120.0
        self.leverage = 15.0
        self.initial_asset = Trade.get_collateral()
        self.JST = pytz.timezone('Asia/Tokyo')
        Trade.cancel_all_orders()
        time.sleep(5)
        self.sync_position_order()

    @jit
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

    @jit
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