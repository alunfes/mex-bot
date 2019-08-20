from Trade import Trade
from datetime import datetime
import pandas as pd

class MexPNL:
    '''
    [{'amount': 1.0,
  'cost': 0.00015957,
  'datetime': '2019-05-10T11:23:06.330Z',
  'fee': {'cost': -3e-08, 'currency': 'USD', 'rate': -0.00025},
  'id': '7f482289-4f63-06d2-99b6-d1d116013215',
  'info': {'account': 243795,
           'avgPx': 6267,
           'clOrdID': '',
           'clOrdLinkID': '',
           'commission': -0.00025,
           'contingencyType': '',
           'cumQty': 1,
           'currency': 'USD',
           'displayQty': None,
           'exDestination': 'XBME',
           'execComm': -3,
           'execCost': -15957,
           'execID': '3d93b50e-2cd6-47ea-301e-6a0fd3c9a276',
           'execInst': '',
           'execType': 'Trade',
           'foreignNotional': -1,
           'homeNotional': 0.00015957,
           'lastLiquidityInd': 'AddedLiquidity',
           'lastMkt': 'XBME',
           'lastPx': 6267,
           'lastQty': 1,
           'leavesQty': 0,
           'multiLegReportingType': 'SingleSecurity',
           'ordRejReason': '',
           'ordStatus': 'Filled',
           'ordType': 'Limit',
           'orderID': '55bb06cb-30e0-38e9-7362-7e9a83733dc1',
           'orderQty': 1,
           'pegOffsetValue': None,
           'pegPriceType': '',
           'price': 6267,
           'settlCurrency': 'XBt',
           'side': 'Buy',
           'simpleCumQty': None,
           'simpleLeavesQty': None,
           'simpleOrderQty': None,
           'stopPx': None,
           'symbol': 'XBTUSD',
           'text': 'Submitted via API.',
           'timeInForce': 'GoodTillCancel',
           'timestamp': '2019-05-10T11:23:06.330Z',
           'tradePublishIndicator': 'PublishTrade',
           'transactTime': '2019-05-10T11:23:06.330Z',
           'trdMatchID': '7f482289-4f63-06d2-99b6-d1d116013215',
           'triggered': '',
           'underlyingLastPx': None,
           'workingIndicator': False},
  'order': '55bb06cb-30e0-38e9-7362-7e9a83733dc1',
  'price': 6267.0,
  'side': 'buy',
  'symbol': 'BTC/USD',
  'takerOrMaker': 'taker',
  'timestamp': 1557487386330,
  'type': None},
    '''
    @classmethod
    def analyze_pnl(cls, result):
        pass



    @classmethod
    def get_month_pnl(cls):
        result = Trade.get_trades(500, datetime(datetime.now().year, datetime.now().month, 1))
        df = pd.DataFrame(result)
        df.to_csv('./pnl.csv')


if __name__ == '__main__':
    Trade.initialize()
    MexPNL.get_month_pnl()