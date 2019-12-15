import ccxt
import time
import json
import csv
import pprint
from datetime import datetime
from SystemFlg import SystemFlg
from LogMaster import LogMaster
import pandas as pd


'''
BitMEX APIのレート制限は、5分間隔（平均1 /秒）ごとに300要求
'''

class Trade:
    @classmethod
    def initialize(cls):
        api_info = open('./ignore/api.json', "r")
        json_data = json.load(api_info)  # JSON形式で読み込む
        id = json_data['id']
        secret = json_data['secret']
        api_info.close()
        cls.bm = ccxt.bitmex({
            'apiKey': id,
            'secret': secret,
        })
        cls.num_private_access = 0
        cls.num_public_access = 0

    @classmethod
    def monitor_api(cls):
        i = 1
        pre_private_access = 0
        pre_public_access = 0
        cls.access_log = []
        cls.total_access_per_300s = 0
        time.sleep(1)
        while SystemFlg.get_system_flg():
            cls.access_log.append(
                cls.num_private_access + cls.num_public_access - pre_private_access - pre_public_access)
            pre_private_access = cls.num_private_access
            pre_public_access = cls.num_public_access
            if i >= 300:
                cls.total_access_per_300s = sum(cls.access_log[-300:])
                cls.access_log.pop(0)
            time.sleep(1)
            i += 1

    '''
    {'BTC': {'free': 0.0149983,
         'total': 0.01500012,
         'used': 1.8199999999995997e-06},
         'free': {'BTC': 0.0149983},
         'info': [{'account': 243795,
           'action': '',
           'amount': 1500000,
           'availableMargin': 1499830,
           'commission': None,
           'confirmedDebit': 0,
           'currency': 'XBt',
           'excessMargin': 1499830,
           'excessMarginPcnt': 1,
           'grossComm': -3,
           'grossExecCost': 15957,
           'grossLastValue': 15948,
           'grossMarkValue': 15948,
           'grossOpenCost': 0,
           'grossOpenPremium': 0,
           'indicativeTax': 0,
           'initMargin': 0,
           'maintMargin': 182,
           'marginBalance': 1500012,
           'marginBalancePcnt': 1,
           'marginLeverage': 0.010631914944680443,
           'marginUsedPcnt': 0.0001,
           'pendingCredit': 0,
           'pendingDebit': 0,
           'prevRealisedPnl': 0,
           'prevState': '',
           'prevUnrealisedPnl': 0,
           'realisedPnl': 3,
           'riskLimit': 1000000000000,
           'riskValue': 15948,
           'sessionMargin': 0,
           'state': '',
           'syntheticMargin': None,
           'targetExcessMargin': 0,
           'taxableMargin': 0,
           'timestamp': '2019-05-10T11:24:30.444Z',
           'unrealisedPnl': 9,
           'unrealisedProfit': 0,
           'varMargin': 0,
           'walletBalance': 1500003,
           'withdrawableMargin': 1499830}],
         'total': {'BTC': 0.01500012},
         'used': {'BTC': 1.8199999999995997e-06}}
    '''
    @classmethod
    def get_balance(cls):
        balance =''
        cls.num_private_access += 1
        try:
            balance = cls.bm.fetch_balance()
        except Exception as e:
            print(e)
        return balance

    '''
    [{'account': 243795,
  'avgCostPrice': 6267,
  'avgEntryPrice': 6267,
  'bankruptPrice': 66.5,
  'breakEvenPrice': 6266,
  'commission': 0.00075,
  'crossMargin': True,
  'currency': 'XBt',
  'currentComm': -3,
  'currentCost': -15957,
  'currentQty': 1,
  'currentTimestamp': '2019-05-10T11:24:30.253Z',
  'deleveragePercentile': 1,
  'execBuyCost': 15957,
  'execBuyQty': 1,
  'execComm': -3,
  'execCost': -15957,
  'execQty': 1,
  'execSellCost': 0,
  'execSellQty': 0,
  'foreignNotional': -1,
  'grossExecCost': 15957,
  'grossOpenCost': 0,
  'grossOpenPremium': 0,
  'homeNotional': 0.00015948,
  'indicativeTax': 0,
  'indicativeTaxRate': None,
  'initMargin': 0,
  'initMarginReq': 0.01,
  'isOpen': True,
  'lastPrice': 6270.34,
  'lastValue': -15948,
  'leverage': 100,
  'liquidationPrice': 66.5,
  'longBankrupt': 0,
  'maintMargin': 182,
  'maintMarginReq': 0.005,
  'marginCallPrice': 66.5,
  'markPrice': 6270.34,
  'markValue': -15948,
  'openOrderBuyCost': 0,
  'openOrderBuyPremium': 0,
  'openOrderBuyQty': 0,
  'openOrderSellCost': 0,
  'openOrderSellPremium': 0,
  'openOrderSellQty': 0,
  'openingComm': 0,
  'openingCost': 0,
  'openingQty': 0,
  'openingTimestamp': '2019-05-10T11:00:00.000Z',
  'posAllowance': 0,
  'posComm': 13,
  'posCost': -15957,
  'posCost2': -15957,
  'posCross': 0,
  'posInit': 160,
  'posLoss': 0,
  'posMaint': 93,
  'posMargin': 173,
  'posState': '',
  'prevClosePrice': 6033.7,
  'prevRealisedPnl': 0,
  'prevUnrealisedPnl': 0,
  'quoteCurrency': 'USD',
  'realisedCost': 0,
  'realisedGrossPnl': 0,
  'realisedPnl': 3,
  'realisedTax': 0,
  'rebalancedPnl': 0,
  'riskLimit': 20000000000,
  'riskValue': 15948,
  'sessionMargin': 0,
  'shortBankrupt': 0,
  'simpleCost': None,
  'simplePnl': None,
  'simplePnlPcnt': None,
  'simpleQty': None,
  'simpleValue': None,
  'symbol': 'XBTUSD',
  'targetExcessMargin': 0,
  'taxBase': 0,
  'taxableMargin': 0,
  'timestamp': '2019-05-10T11:24:30.253Z',
  'underlying': 'XBT',
  'unrealisedCost': -15957,
  'unrealisedGrossPnl': 9,
  'unrealisedPnl': 9,
  'unrealisedPnlPcnt': 0.0006,
  'unrealisedRoePcnt': 0.0564,
  'unrealisedTax': 0,
  'varMargin': 0}]
    '''
    @classmethod
    def get_positions(cls):  # None
        cls.num_private_access += 1
        try:
            positions = cls.bm.private_get_position()
        except Exception as e:
            print('error in get_positions ' + e)
        return positions

    '''
            {'ask': 6049.0,
         'askVolume': None,
         'average': 5929.5,
         'baseVolume': 448032.43519207294,
         'bid': 6048.5,
         'bidVolume': None,
         'change': 240.0,
         'close': 6049.5,
         'datetime': '2019-05-09T06:19:25.837Z',
         'high': 6095.5,
         'info': {'askPrice': 6049,
          'bankruptLimitDownPrice': None,
          'bankruptLimitUpPrice': None,
          'bidPrice': 6048.5,
          'buyLeg': '',
          'calcInterval': None,
          'capped': False,
          'closingTimestamp': '2019-05-09T07:00:00.000Z',
          'deleverage': True,
          'expiry': None,
          'fairBasis': -3.05,
          'fairBasisRate': -0.776355,
          'fairMethod': 'FundingRate',
          'fairPrice': 6047.8,
          'foreignNotional24h': 2656455860,
          'front': '2016-05-13T12:00:00.000Z',
          'fundingBaseSymbol': '.XBTBON8H',
          'fundingInterval': '2000-01-01T08:00:00.000Z',
          'fundingPremiumSymbol': '.XBTUSDPI8H',
          'fundingQuoteSymbol': '.USDBON8H',
          'fundingRate': -0.000709,
          'fundingTimestamp': '2019-05-09T12:00:00.000Z',
          'hasLiquidity': True,
          'highPrice': 6095.5,
          'homeNotional24h': 448032.43519207294,
          'impactAskPrice': 6049.6068,
          'impactBidPrice': 6048.5,
          'impactMidPrice': 6049,
          'indicativeFundingRate': -0.000421,
          'indicativeSettlePrice': 6050.85,
          'indicativeTaxRate': 0,
          'initMargin': 0.01,
          'insuranceFee': 0,
          'inverseLeg': '',
          'isInverse': True,
          'isQuanto': False,
          'lastChangePcnt': 0.0413,
          'lastPrice': 6049.5,
          'lastPriceProtected': 6049.5,
          'lastTickDirection': 'ZeroPlusTick',
          'limit': None,
          'limitDownPrice': None,
          'limitUpPrice': None,
          'listing': '2016-05-13T12:00:00.000Z',
          'lotSize': 1,
          'lowPrice': 5785,
          'maintMargin': 0.005,
          'makerFee': -0.00025,
          'markMethod': 'FairPrice',
          'markPrice': 6047.8,
          'maxOrderQty': 10000000,
          'maxPrice': 1000000,
          'midPrice': 6048.75,
          'multiplier': -100000000,
          'openInterest': 599731344,
          'openValue': 9916557773040,
          'openingTimestamp': '2019-05-09T06:00:00.000Z',
          'optionMultiplier': None,
          'optionStrikePcnt': None,
          'optionStrikePrice': None,
          'optionStrikeRound': None,
          'optionUnderlyingPrice': None,
          'positionCurrency': 'USD',
          'prevClosePrice': 5844.78,
          'prevPrice24h': 5809.5,
          'prevTotalTurnover': 18748139392500940,
          'prevTotalVolume': 1163662790027,
          'publishInterval': None,
          'publishTime': None,
          'quoteCurrency': 'USD',
          'quoteToSettleMultiplier': None,
          'rebalanceInterval': None,
          'rebalanceTimestamp': None,
          'reference': 'BMEX',
          'referenceSymbol': '.BXBT',
          'relistInterval': None,
          'riskLimit': 20000000000,
          'riskStep': 10000000000,
          'rootSymbol': 'XBT',
          'sellLeg': '',
          'sessionInterval': '2000-01-01T01:00:00.000Z',
          'settlCurrency': 'XBt',
          'settle': None,
          'settledPrice': None,
          'settlementFee': 0,
          'state': 'Open',
          'symbol': 'XBTUSD',
          'takerFee': 0.00075,
          'taxed': True,
          'tickSize': 0.5,
          'timestamp': '2019-05-09T06:19:25.837Z',
          'totalTurnover': 18748719605575164,
          'totalVolume': 1163697822836,
          'turnover': 580213074224,
          'turnover24h': 44803243519207,
          'typ': 'FFWCSX',
          'underlying': 'XBT',
          'underlyingSymbol': 'XBT=',
          'underlyingToPositionMultiplier': None,
          'underlyingToSettleMultiplier': -100000000,
          'volume': 35032809,
          'volume24h': 2656455860,
          'vwap': 5929.4397},
         'last': 6049.5,
         'low': 5785.0,
         'open': 5809.5,
         'percentage': 4.1311644719855405,
         'previousClose': None,
         'quoteVolume': 2656455860.0,
         'symbol': 'BTC/USD',
         'timestamp': 1557382765837,
         'vwap': 5929.4397}
    '''
    @classmethod
    def get_ticker(cls):
        cls.num_public_access += 1
        try:
            tick = cls.bm.fetch_ticker('BTC/USD')
        except Exception as e:
            print('error in get_ticker ' +str(e))
        return tick


    '''
    {'BTC': {'free': 0.015000000000000001,
         'total': 0.015000000000000001,
         'used': 0.0},
         'free': {'BTC': 0.015000000000000001},
         'info': [{'account': 243795,
           'action': '',
           'amount': 1500000,
           'availableMargin': 1500000,
           'commission': None,
           'confirmedDebit': 0,
           'currency': 'XBt',
           'excessMargin': 1500000,
           'excessMarginPcnt': 1,
           'grossComm': 0,
           'grossExecCost': 0,
           'grossLastValue': 0,
           'grossMarkValue': 0,
           'grossOpenCost': 0,
           'grossOpenPremium': 0,
           'indicativeTax': 0,
           'initMargin': 0,
           'maintMargin': 0,
           'marginBalance': 1500000,
           'marginBalancePcnt': 1,
           'marginLeverage': 0,
           'marginUsedPcnt': 0,
           'pendingCredit': 0,
           'pendingDebit': 0,
           'prevRealisedPnl': 0,
           'prevState': '',
           'prevUnrealisedPnl': 0,
           'realisedPnl': 0,
           'riskLimit': 1000000000000,
           'riskValue': 0,
           'sessionMargin': 0,
           'state': '',
           'syntheticMargin': None,
           'targetExcessMargin': 0,
           'taxableMargin': 0,
           'timestamp': '2019-05-10T06:31:16.276Z',
           'unrealisedPnl': 0,
           'unrealisedProfit': 0,
           'varMargin': 0,
           'walletBalance': 1500000,
           'withdrawableMargin': 1500000}],
         'total': {'BTC': 0.015000000000000001},
         'used': {'BTC': 0.0}}
    '''
    @classmethod
    def get_collateral(cls):
        cls.num_private_access += 1
        res = ''
        try:
            res = cls.bm.fetch_balance()
        except Exception as e:
            print('error in get_collateral ' +str(e))
        return res



    '''
    {'amount': 1.0,
     'average': None,
     'cost': 0.0,
     'datetime': '2019-05-09T12:23:45.906Z',
     'fee': None,
     'filled': 0.0,
     'id': 'b95fb710-3a98-72fa-6a88-2fe2efc68dc2',
     'info': {'account': 243795,
          'avgPx': None,
          'clOrdID': '',
          'clOrdLinkID': '',
          'contingencyType': '',
          'cumQty': 0,
          'currency': 'USD',
          'displayQty': None,
          'exDestination': 'XBME',
          'execInst': '',
          'leavesQty': 1,
          'multiLegReportingType': 'SingleSecurity',
          'ordRejReason': '',
          'ordStatus': 'New',
          'ordType': 'Limit',
          'orderID': 'b95fb710-3a98-72fa-6a88-2fe2efc68dc2',
          'orderQty': 1,
          'pegOffsetValue': None,
          'pegPriceType': '',
          'price': 5000,
          'settlCurrency': 'XBt',
          'side': 'Buy',
          'simpleCumQty': None,
          'simpleLeavesQty': None,
          'simpleOrderQty': None,
          'stopPx': None,
          'symbol': 'XBTUSD',
          'text': 'Submitted via API.',
          'timeInForce': 'GoodTillCancel',
          'timestamp': '2019-05-09T12:23:45.906Z',
          'transactTime': '2019-05-09T12:23:45.906Z',
          'triggered': '',
          'workingIndicator': True},
         'lastTradeTimestamp': 1557404625906,
         'price': 5000.0,
         'remaining': 1.0,
         'side': 'buy',
         'status': 'open',
         'symbol': 'BTC/USD',
         'timestamp': 1557404625906,
         'type': 'limit'}
    '''
    @classmethod
    def order(cls, side, price, type, amount):
        order_info = ''
        try:
            order_info = cls.bm.create_order(
                symbol='BTC/USD',
                type=type,
                side=side,
                price=price,
                amount=amount  #×0.0001btc
            )
        except Exception as e:
            print('Trade-order error!, '+str(e))
        return order_info

    '''
    {'amount': 1.0,
     'average': None,
     'cost': 0.0,
     'datetime': '2019-05-09T12:26:12.574Z',
     'fee': None,
     'filled': 0.0,
     'id': 'b95fb710-3a98-72fa-6a88-2fe2efc68dc2',
     'info': {'account': 243795,
          'avgPx': None,
          'clOrdID': '',
          'clOrdLinkID': '',
          'contingencyType': '',
          'cumQty': 0,
          'currency': 'USD',
          'displayQty': None,
          'exDestination': 'XBME',
          'execInst': '',
          'leavesQty': 0,
          'multiLegReportingType': 'SingleSecurity',
          'ordRejReason': '',
          'ordStatus': 'Canceled',
          'ordType': 'Limit',
          'orderID': 'b95fb710-3a98-72fa-6a88-2fe2efc68dc2',
          'orderQty': 1,
          'pegOffsetValue': None,
          'pegPriceType': '',
          'price': 5000,
          'settlCurrency': 'XBt',
          'side': 'Buy',
          'simpleCumQty': None,
          'simpleLeavesQty': None,
          'simpleOrderQty': None,
          'stopPx': None,
          'symbol': 'XBTUSD',
          'text': 'Canceled: Canceled via API.\nSubmitted via API.',
          'timeInForce': 'GoodTillCancel',
          'timestamp': '2019-05-09T12:26:12.574Z',
          'transactTime': '2019-05-09T12:23:45.906Z',
          'triggered': '',
          'workingIndicator': False},
         'lastTradeTimestamp': 1557404625906,
         'price': 5000.0,
         'remaining': 1.0,
         'side': 'buy',
         'status': 'canceled',
         'symbol': 'BTC/USD',
         'timestamp': 1557404772574,
         'type': 'limit'}
    '''
    @classmethod
    def cancel_order(cls, order_id):
        cls.num_private_access += 1
        cancel = ''
        try:
            cancel = cls.bm.cancel_order(id=order_id, symbol='BTC/USD')
        except Exception as e:
            print('error in cancel_order ' + str(e), cancel)
            LogMaster.add_log({'dt': datetime.now(), 'api_error': 'Trade-get cancel_order error! ' + str(e)})
        return cancel

    @classmethod
    def cancel_and_wait_completion(cls, order_id):
        cancel = cls.cancel_order(order_id)
        if len(cancel) > 0:
            if cancel['info']['ordStatus'] == 'Canceled':
                return 0
            else:
                time.sleep(1)
                return cls.cancel_and_wait_completion(order_id)
        print('Trade - cancel_and_wait_completion - unexpected error!')
        LogMaster.add_log({'dt': datetime.now(), 'api_error': 'Trade - cancel_and_wait_completion - unexpected error!'})
        return -1

    '''
    [{'amount': 1.0,
      'average': None,
      'cost': 0.0,
      'datetime': '2019-05-10T11:18:20.965Z',
      'fee': None,
      'filled': 0.0,
      'id': '55bb06cb-30e0-38e9-7362-7e9a83733dc1',
      'info': {'account': 243795,
           'avgPx': None,
           'clOrdID': '',
           'clOrdLinkID': '',
           'contingencyType': '',
           'cumQty': 0,
           'currency': 'USD',
           'displayQty': None,
           'exDestination': 'XBME',
           'execInst': '',
           'leavesQty': 1,
           'multiLegReportingType': 'SingleSecurity',
           'ordRejReason': '',
           'ordStatus': 'New',
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
           'timestamp': '2019-05-10T11:18:20.965Z',
           'transactTime': '2019-05-10T11:18:20.965Z',
           'triggered': '',
           'workingIndicator': True},
          'lastTradeTimestamp': 1557487100965,
          'price': 6267.0,
          'remaining': 1.0,
          'side': 'buy',
          'status': 'open',
          'symbol': 'BTC/USD',
          'timestamp': 1557487100965,
          'type': 'limit'}]
    '''
    @classmethod
    def get_open_orders(cls):
        cls.num_private_access += 1
        try:
            orders = cls.bm.fetch_open_orders()
        except Exception as e:
            print('error in get_orders ' + str(e))
        return orders


    #get historical order data of a specific order id.
    '''
    [{'info': {'orderID': 'ffe83f3e-10be-3d0a-fe04-22a69437b849', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7219, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7219, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-13T13:32:39.844Z', 'timestamp': '2019-12-13T13:33:20.742Z'}, 'id': 'ffe83f3e-10be-3d0a-fe04-22a69437b849', 'timestamp': 1576244000742, 'datetime': '2019-12-13T13:33:20.742Z', 'lastTradeTimestamp': 1576243959844, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 7219.0, 'amount': 10.0, 'cost': 72190.0, 'average': 7219.0, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': 'f5019d9e-f9ab-4986-59d4-6a7d0be13a5c', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 50, 'price': 7224, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 50, 'avgPx': 7224, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-12-13T13:43:38.880Z', 'timestamp': '2019-12-13T13:43:38.880Z'}, 'id': 'f5019d9e-f9ab-4986-59d4-6a7d0be13a5c', 'timestamp': 1576244618880, 'datetime': '2019-12-13T13:43:38.880Z', 'lastTradeTimestamp': 1576244618880, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 7224.0, 'amount': 50.0, 'cost': 361200.0, 'average': 7224.0, 'filled': 50.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': '6dfdd402-0831-509b-1bc8-68b5e7f7443f', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7241.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7241.5, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-14T08:09:31.044Z', 'timestamp': '2019-12-14T08:09:31.044Z'}, 'id': '6dfdd402-0831-509b-1bc8-68b5e7f7443f', 'timestamp': 1576310971044, 'datetime': '2019-12-14T08:09:31.044Z', 'lastTradeTimestamp': 1576310971044, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 7241.5, 'amount': 10.0, 'cost': 72415.0, 'average': 7241.5, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': 'abeb3acb-9e75-c454-1a36-08776e241982', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7178, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7178.25, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-14T09:06:40.720Z', 'timestamp': '2019-12-14T09:06:49.994Z'}, 'id': 'abeb3acb-9e75-c454-1a36-08776e241982', 'timestamp': 1576314409994, 'datetime': '2019-12-14T09:06:49.994Z', 'lastTradeTimestamp': 1576314400720, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 7178.0, 'amount': 10.0, 'cost': 71782.5, 'average': 7178.25, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': 'c1ae867c-7a88-7584-1f32-3b6a2c49eb0c', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7186.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7186.5, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-14T09:17:20.255Z', 'timestamp': '2019-12-14T09:17:20.255Z'}, 'id': 'c1ae867c-7a88-7584-1f32-3b6a2c49eb0c', 'timestamp': 1576315040255, 'datetime': '2019-12-14T09:17:20.255Z', 'lastTradeTimestamp': 1576315040255, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 7186.5, 'amount': 10.0, 'cost': 71865.0, 'average': 7186.5, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': '890694ee-7eaa-bf36-2bbd-ec6a430eaeb9', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7181.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7181.5, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-14T09:31:39.348Z', 'timestamp': '2019-12-14T09:31:39.348Z'}, 'id': '890694ee-7eaa-bf36-2bbd-ec6a430eaeb9', 'timestamp': 1576315899348, 'datetime': '2019-12-14T09:31:39.348Z', 'lastTradeTimestamp': 1576315899348, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 7181.5, 'amount': 10.0, 'cost': 71815.0, 'average': 7181.5, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': 'e19c4273-a6ba-9a6a-f6e2-2e9a23640059', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7036.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7036.5, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-15T01:01:37.654Z', 'timestamp': '2019-12-15T01:01:37.654Z'}, 'id': 'e19c4273-a6ba-9a6a-f6e2-2e9a23640059', 'timestamp': 1576371697654, 'datetime': '2019-12-15T01:01:37.654Z', 'lastTradeTimestamp': 1576371697654, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 7036.5, 'amount': 10.0, 'cost': 70365.0, 'average': 7036.5, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': '40be7947-a40f-b8a0-81ef-c9939b221a08', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7040, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 10, 'avgPx': 7040, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-15T01:13:50.846Z', 'timestamp': '2019-12-15T01:13:50.846Z'}, 'id': '40be7947-a40f-b8a0-81ef-c9939b221a08', 'timestamp': 1576372430846, 'datetime': '2019-12-15T01:13:50.846Z', 'lastTradeTimestamp': 1576372430846, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 7040.0, 'amount': 10.0, 'cost': 70400.0, 'average': 7040.0, 'filled': 10.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}, 
    {'info': {'orderID': '114a7300-ece3-cfe4-17d6-2749c96f1172', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 40, 'price': 7136, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 40, 'avgPx': 7136.25, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-12-15T08:48:06.681Z', 'timestamp': '2019-12-15T08:57:45.558Z'}, 'id': '114a7300-ece3-cfe4-17d6-2749c96f1172', 'timestamp': 1576400265558, 'datetime': '2019-12-15T08:57:45.558Z', 'lastTradeTimestamp': 1576399686681, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 7136.0, 'amount': 40.0, 'cost': 285450.0, 'average': 7136.25, 'filled': 40.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}]
    '''
    @classmethod
    def get_order_byid(cls, order_id):
        cls.num_private_access += 1
        orders = None
        count = 50
        try:
            orders = cls.bm.fetch_orders(symbol='BTC/USD', since=None, limit=None, params={'count': count, 'reverse': True})
            if len(order_id) > 0:
                orders = map(lambda x: x['info'] if x['info']['orderID'] == order_id else {}, orders)
                orders = [x for x in orders if x != {}]
                if len(orders) == 0:
                    order_id = None
        except Exception as e:
            print('error in get_order_byid' + str(e))
        return orders


    @classmethod
    def get_trades(cls,count):
        cls.num_private_access += 1
        trades = None
        try:
            #trades = cls.bm.fetch_my_trades(symbol='BTC/USD', since=None, limit=None,  params={'startTime':startTime,'count':count})
            trades = cls.bm.fetch_my_trades(symbol='BTC/USD', since=None, limit=None,params={'count': count, 'reverse':True})
        except Exception as e:
            print('error in get_trades ' + str(e))
        return trades

    @classmethod
    def get_private_execution_trade(cls, count, start_time):
        cls.num_private_access += 1
        try:
            trades = cls.bm.privateGetExecutionTradeHistory(symbol='BTC/USD', since=None, limit=None, params={'startTime': start_time, 'count': count})
        except Exception as e:
            print('error in get_trades ' + str(e))
        return trades


if __name__ == '__main__':
    Trade.initialize()
    LogMaster.initialize()

    print(Trade.bm.fetch_orders(symbol='BTC/USD', since=None, limit=None,params={'count': 10, 'reverse':True}))

    #pprint.pprint(Trade.get_orders())
    #pprint.pprint(Trade.get_positions())
    #pprint.pprint(Trade.get_balance())
    #pprint.pprint(Trade.get_collateral())


    '''
    result = Trade.get_trades(100, datetime(2019, 7, 1))
    df = pd.DataFrame(result)
    pprint.pprint(df)
    df.to_csv('./trade_hist.csv')
    '''

    #pprint.pprint(Trade.get_collateral())
    #order = Trade.order('buy',5000,1)
    ##pprint.pprint(Trade.get_orders())
    #pprint.pprint(Trade.cancel_order(order['id']))
    #pprint.pprint(Trade.get_ticker())