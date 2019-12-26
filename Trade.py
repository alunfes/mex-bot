import ccxt
import time
import json
import csv
import pprint
from datetime import datetime
from SystemFlg import SystemFlg
from LogMaster import LogMaster
from LineNotification import LineNotification
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
        cls.error_trial = 5
        cls.rest_interval = 1


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
        for i in range(cls.error_trial):
            cls.num_private_access += 1
            order_info = ''
            error_message = ''
            try:
                if type == 'Limit':
                    order_info = cls.bm.create_order(
                        symbol='BTC/USD',
                        type=type,
                        side=side,
                        price=price,
                        amount=amount  #×0.0001btc
                    )
                elif type == 'Market':
                    order_info = cls.bm.create_order(
                        symbol='BTC/USD',
                        type=type,
                        side=side,
                        amount=amount  # ×0.0001btc
                    )
            except Exception as e:
                error_message = str(e)
                print('Trade-order error!, '+str(e))
                print('side=',side, ', price=',price, ', type', type, ', amount', amount)
                LineNotification.send_error('error in order! ' + '\r\n' + order_info + '\r\n' + str(e))
            finally:
                if 'error' not in error_message:
                    return order_info
                else:
                    time.sleep(cls.rest_interval)
        return None

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
        for i in range(cls.error_trial):
            cls.num_private_access += 1
            cancel = ''
            error_message = ''
            try:
                cancel = cls.bm.cancel_order(id=order_id, symbol='BTC/USD')
            except Exception as e:
                error_message = str(e)
                print('error in cancel_order ' + str(e), cancel)
                LogMaster.add_log({'dt': datetime.now(), 'api_error': 'Trade-get cancel_order error! ' + str(e)})
                LineNotification.send_error('error in cancel order! ' + '\r\n' + cancel + '\r\n' + str(e))
            finally:
                if 'error' not in error_message:
                    return cancel
                else:
                    time.sleep(cls.rest_interval)
        return None

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
    def get_order_byid(cls, order_id, count):
        cls.num_private_access += 1
        orders = None
        try:
            orders = cls.bm.fetch_orders(symbol='BTC/USD', since=None, limit=None, params={'count': count, 'reverse': True})
            if len(order_id) > 0:
                orders = map(lambda x: x['info'] if x['info']['orderID'] == order_id else {}, orders)
                orders = [x for x in orders if x != {}]
                if len(orders) == 0:
                    order_id = None
        except Exception as e:
            print('error in get_order_byid' + str(e))
            LineNotification.send_error('error in get_order_byid! '  + '\r\n' + str(e))
        return orders

    '''
    [{'info': {'execID': '891dac5d-08c2-ab94-9cda-fa5e0a2e67e8', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 500, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 107051, 'simpleCumQty': None, 'cumQty': 192949, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '92c70d6b-868d-4872-b014-eb9bdfbdda63', 'execCost': 6564500, 'execComm': -1641, 'homeNotional': -0.065645, 'foreignNotional': 500, 'transactTime': '2019-12-23T02:00:30.761Z', 'timestamp': '2019-12-23T02:00:30.761Z'}, 'timestamp': 1577066430761, 'datetime': '2019-12-23T02:00:30.761Z', 'symbol': 'BTC/USD', 'id': '92c70d6b-868d-4872-b014-eb9bdfbdda63', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.065645, 'amount': 500.0, 'fee': {'cost': -1.641e-05, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'e0a106ca-3b12-cdc7-e600-0bb5e23038e2', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 1000, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 106051, 'simpleCumQty': None, 'cumQty': 193949, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '55f5962a-2e08-1743-c265-758cdfdad591', 'execCost': 13129000, 'execComm': -3282, 'homeNotional': -0.13129, 'foreignNotional': 1000, 'transactTime': '2019-12-23T02:00:31.059Z', 'timestamp': '2019-12-23T02:00:31.059Z'}, 'timestamp': 1577066431059, 'datetime': '2019-12-23T02:00:31.059Z', 'symbol': 'BTC/USD', 'id': '55f5962a-2e08-1743-c265-758cdfdad591', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.13129, 'amount': 1000.0, 'fee': {'cost': -3.282e-05, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'bcb65f68-f299-af87-d079-a751481b09ba', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 645, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 105406, 'simpleCumQty': None, 'cumQty': 194594, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': 'b014fdc0-589e-e9e9-2e91-6e6ddd1d1146', 'execCost': 8468205, 'execComm': -2117, 'homeNotional': -0.08468205, 'foreignNotional': 645, 'transactTime': '2019-12-23T02:00:31.373Z', 'timestamp': '2019-12-23T02:00:31.373Z'}, 'timestamp': 1577066431373, 'datetime': '2019-12-23T02:00:31.373Z', 'symbol': 'BTC/USD', 'id': 'b014fdc0-589e-e9e9-2e91-6e6ddd1d1146', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.08468205, 'amount': 645.0, 'fee': {'cost': -2.117e-05, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'a3412f80-dd34-c767-1705-eec8b5ef2884', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 50000, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 55406, 'simpleCumQty': None, 'cumQty': 244594, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': 'a7157d88-f78f-0bb8-228d-81f92a8eba4d', 'execCost': 656450000, 'execComm': -164112, 'homeNotional': -6.5645, 'foreignNotional': 50000, 'transactTime': '2019-12-23T02:00:33.784Z', 'timestamp': '2019-12-23T02:00:33.784Z'}, 'timestamp': 1577066433784, 'datetime': '2019-12-23T02:00:33.784Z', 'symbol': 'BTC/USD', 'id': 'a7157d88-f78f-0bb8-228d-81f92a8eba4d', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 6.5645, 'amount': 50000.0, 'fee': {'cost': -0.00164112, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'a7ba42ae-a20b-02b4-e421-1e5772f2d900', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 1200, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 54206, 'simpleCumQty': None, 'cumQty': 245794, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': 'fb4ad3b7-8342-1c3d-88af-2e38c41c570d', 'execCost': 15754800, 'execComm': -3938, 'homeNotional': -0.157548, 'foreignNotional': 1200, 'transactTime': '2019-12-23T02:00:34.023Z', 'timestamp': '2019-12-23T02:00:34.023Z'}, 'timestamp': 1577066434023, 'datetime': '2019-12-23T02:00:34.023Z', 'symbol': 'BTC/USD', 'id': 'fb4ad3b7-8342-1c3d-88af-2e38c41c570d', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.157548, 'amount': 1200.0, 'fee': {'cost': -3.938e-05, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': '343e5385-2eea-8fb7-75d3-dc04e152c825', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 10000, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 44206, 'simpleCumQty': None, 'cumQty': 255794, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '8c9cd8ff-cc65-dada-bfc2-bcf3a5319033', 'execCost': 131290000, 'execComm': -32822, 'homeNotional': -1.3129, 'foreignNotional': 10000, 'transactTime': '2019-12-23T02:00:34.296Z', 'timestamp': '2019-12-23T02:00:34.296Z'}, 'timestamp': 1577066434296, 'datetime': '2019-12-23T02:00:34.296Z', 'symbol': 'BTC/USD', 'id': '8c9cd8ff-cc65-dada-bfc2-bcf3a5319033', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 1.3129, 'amount': 10000.0, 'fee': {'cost': -0.00032822, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'b73d321b-a75e-0dbe-234f-ac52ef66c113', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 5000, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 39206, 'simpleCumQty': None, 'cumQty': 260794, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '5ae9ae75-3398-e297-07c2-14aefdb5e1fb', 'execCost': 65645000, 'execComm': -16411, 'homeNotional': -0.65645, 'foreignNotional': 5000, 'transactTime': '2019-12-23T02:00:34.554Z', 'timestamp': '2019-12-23T02:00:34.554Z'}, 'timestamp': 1577066434554, 'datetime': '2019-12-23T02:00:34.554Z', 'symbol': 'BTC/USD', 'id': '5ae9ae75-3398-e297-07c2-14aefdb5e1fb', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.65645, 'amount': 5000.0, 'fee': {'cost': -0.00016411, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': '8135ed27-431b-5fd3-a2e5-7c381c161862', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 5000, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 34206, 'simpleCumQty': None, 'cumQty': 265794, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '915af080-b81c-ee66-6062-5a60e305fa5e', 'execCost': 65645000, 'execComm': -16411, 'homeNotional': -0.65645, 'foreignNotional': 5000, 'transactTime': '2019-12-23T02:00:36.121Z', 'timestamp': '2019-12-23T02:00:36.121Z'}, 'timestamp': 1577066436121, 'datetime': '2019-12-23T02:00:36.121Z', 'symbol': 'BTC/USD', 'id': '915af080-b81c-ee66-6062-5a60e305fa5e', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.65645, 'amount': 5000.0, 'fee': {'cost': -0.00016411, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'a8dd345d-0955-8983-b145-c437ab449769', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 1250, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 32956, 'simpleCumQty': None, 'cumQty': 267044, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '8400b80a-7c4d-b142-e41e-a5f088144ba9', 'execCost': 16411250, 'execComm': -4102, 'homeNotional': -0.1641125, 'foreignNotional': 1250, 'transactTime': '2019-12-23T02:00:36.410Z', 'timestamp': '2019-12-23T02:00:36.410Z'}, 'timestamp': 1577066436410, 'datetime': '2019-12-23T02:00:36.410Z', 'symbol': 'BTC/USD', 'id': '8400b80a-7c4d-b142-e41e-a5f088144ba9', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 0.1641125, 'amount': 1250.0, 'fee': {'cost': -4.102e-05, 'currency': 'BTC', 'rate': -0.00025}}, 
    {'info': {'execID': 'f366df8b-fdb7-864c-56c9-dd1168a1d0ce', 'orderID': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 32956, 'lastPx': 7617, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 300000, 'price': 7617, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 300000, 'avgPx': 7617, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': 'baba7b83-4453-aa4f-89d0-e596aeb7dde0', 'execCost': 432679324, 'execComm': -108169, 'homeNotional': -4.32679324, 'foreignNotional': 32956, 'transactTime': '2019-12-23T02:00:37.119Z', 'timestamp': '2019-12-23T02:00:37.119Z'}, 'timestamp': 1577066437119, 'datetime': '2019-12-23T02:00:37.119Z', 'symbol': 'BTC/USD', 'id': 'baba7b83-4453-aa4f-89d0-e596aeb7dde0', 'order': 'a49b56a1-d3ad-9ddd-af2e-67906ea042a7', 'type': 'limit', 'takerOrMaker': 'taker', 'side': 'sell', 'price': 7617.0, 'cost': 4.32679324, 'amount': 32956.0, 'fee': {'cost': -0.00108169, 'currency': 'BTC', 'rate': -0.00025}}]
    '''
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
    LineNotification.initialize()
    LogMaster.initialize()

    Trade.cancel_order('44')



    #order = Trade.order('Buy', 5000, 'Limit', 10)
    #print(Trade.cancel_order(order['info']['orderID']))

    #print(Trade.bm.fetch_orders(symbol='BTC/USD', since=None, limit=None,params={'count': 10, 'reverse':True}))

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