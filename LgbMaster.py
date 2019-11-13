
'''
・calc index and generate df on every 60 min
・generate train, valid data and train lgm model
・save model and col_list with name of latest dt
'''

import threading
import time
from datetime import datetime, timedelta, timezone
from SimLgbModel import LgbModel
from SystemFlg import SystemFlg

class LgbMaster:
    def lgbmaster_thread(self):
        while SystemFlg.get_system_flg():
            if datetime.now().minute is 0:
                pass
            time.sleep(1)