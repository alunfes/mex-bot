import threading

class Account:
    def __init__(self):
        self.lock_posi = threading.Lock()
        self.lock_order = threading.Lock()
        self.posi_side = ''
        self.posi_price = 0
        self.posi_size = 0
        self.order_ids = []
        self.order_side = {}
        self.order_price = {}
        self.order_size = {}
        self.exec_id = []
        self.realized_pnl = 0
        self.unrealized_pnl = 0
        self.num_trade = 0

    def add_order(self, order_id, side, price, size):
        with self.lock_order:
            self.order_ids.append(order_id)
            self.order_side[order_id] = side
            self.order_price[order_id] = price
            self.order_size[order_id] = size

    def remove_order(self, order_id):
        with self.lock_order:
            self.order_ids.remove(order_id)
            del self.order_size[order_id]
            del self.order_price[order_id]

    def execute_order(self, order_id, exec_id, exec_side, exec_price, leaves_size):
        if order_id in self.order_ids:
            self.exec_id.append(exec_id)
            self.__calc_pnl(exec_side, exec_price, self.order_size[order_id] - leaves_size)
            self.__update_position(exec_side, exec_price, self.order_size[order_id] - leaves_size)
            if leaves_size > 0:
                self.order_size[order_id] = leaves_size
            else:
                self.remove_order(order_id)

    def __calc_pnl(self, exec_side, exec_price, exec_size):
        if self.posi_side != exec_side:
            self.realized_pnl += (exec_price - self.posi_price) * exec_size if self.posi_side == 'Buy' else (self.posi_price - exec_price) * exec_size

    def calc_unrealized_pnl(self, ltp):
        self.unrealized_pnl = (ltp - self.posi_price) * self.posi_size if self.posi_side == 'Buy' else (self.posi_price - ltp) * self.posi_size



    def __update_position(self, side, price, size):
        with self.lock_posi:
            if self.posi_side =='':
                self.posi_side = side
                self.posi_price = price
                self.posi_size = size
            elif self.posi_side == side:
                self.posi_price = ((self.posi_price * self.posi_size) + (price * size)) / (self.posi_size + size)
                self.posi_size += size
            else: #opposite side trade
                self.posi_side = side
                self.posi_size = size - self.posi_size
                self.posi_price = price











