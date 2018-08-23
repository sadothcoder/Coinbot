import datetime
import urllib
import urllib.parse
import urllib.request
import pprint as pp

from collections import defaultdict
from .utils import createSign, http_get_request, http_post_request
from ..exchange import Exchange


class Huobi(Exchange):
    def __init__(self, key, secret):
        self.api = HuobiAPI(key, secret)
        self.all_pairs = self.get_all_trading_pairs()
        super().__init__('huobi')
        self.connect_success()

    def get_pair(self, coin, base):
        return (coin + base).lower()

    def get_all_trading_pairs(self):
        # ***** this needs to change form to updated one ***** #
        all_pairs = set()
        res = self.api.get_symbols()['data']
        for info in res:
            coin = info['base-currency']
            base = info['quote-currency']
            all_pairs.add(self.get_pair(coin, base))
        return all_pairs

    def get_all_trading_coins(self):
        # ***** this needs to change form to updated one ***** #
        all_coins = set()
        res = self.api.get_symbols()['data']
        for info in res:
            coin = info['base-currency']
            all_coins.add(coin)
        return all_coins

    def get_BTC_price(self):
        return self.get_price('BTC', base='USDT')

    def get_price(self, coin, base='BTC', _type=0):
        TYPES = {0: 'bid', 1: 'ask'}
        pair = self.get_pair(coin, base)
        if pair in self.all_pairs:
            return float(self.api.get_ticker(symbol=pair)['tick'][TYPES[_type]][0])
        else:
            return 0

    def get_full_balance(self, allow_zero=False):
        BTC_price = self.get_BTC_price()
        coins = {
            'total': {'BTC': 0, 'USD': 0, 'num': 0},
            'USD': {'BTC': 0, 'USD': 0, 'num': 0}
        }
        for coinName, num in self.coins.items():
            coinName = coinName.upper()
            if allow_zero or num != 0:
                if coinName == 'USDT':
                    coinName = 'USD'
                    BTC_value = num / BTC_price
                elif coinName == 'BTC':
                    BTC_value = num
                else:
                    BTC_value = self.get_price(coinName) * num
                USD_value = BTC_value * BTC_price

                # update info
                coins[coinName] = {
                    'num': num,
                    'BTC': BTC_value,
                    'USD': USD_value
                }
                coins['total']['BTC'] += BTC_value
                coins['total']['USD'] += USD_value
        return coins

    def get_all_coin_balance(self, allow_zero=False):
        balances = self.api.get_balance()
        coins = defaultdict(float)
        for coin in balances:
            coinName = coin['currency']
            num = float(coin['balance'])
            if coinName == 'USDT':
                coinName = 'USD'
            if allow_zero or num != 0:
                coins[coinName] += num
        return dict(coins)

    # def market_buy(self, coin, base='BTC', quantity=0):
    #     pair = self.get_pair(coin, base)
    #     response = self.api.order_market_buy(symbol=pair, quantity=quantity)
    #     return {
    #         'exchange': self.name,
    #         'side': 'sell',
    #         'pair': self.get_my_pair(coin, base),
    #         'price': response['price'],
    #         'quantity': response['executedQty'],
    #         'total': None,
    #         'fee': None,
    #         'id': response['orderId'],
    #         'id2': response['clientOrderId']
    #     }

    # def market_sell(self, coin, base='BTC', quantity=0):
    #     pair = self.get_pair(coin, base)
    #     response = self.api.order_market_sell(symbol=pair, quantity=quantity)
    #     return {
    #         'exchange': self.name,
    #         'side': 'sell',
    #         'pair': self.get_my_pair(coin, base),
    #         'price': response['price'],
    #         'quantity': response['executedQty'],
    #         'total': None,
    #         'fee': None,
    #         'id': response['orderId'],
    #         'id2': response['clientOrderId']
    #     }

    # def market_sell_all(self, coin, base='BTC'):
    #     quantity = self.get_coin_balance(coin)
    #     if quantity <= 0:
    #         print('%s does not have enough balance to sell')
    #         return None
    #     else:
    #         step = self.get_step_size(self.get_pair(coin, base))
    #         if step > 0 and quantity >= step:
    #             quantity = quantity - (quantity % float(step))
    #             return self.market_sell(coin, base=base, quantity=quantity)


# ------------------------------------------------------------------ #
# --------------------------- API Wrapper -------------------------- #
# ------------------------------------------------------------------ #
class HuobiAPI:
    # API 请求地址
    MARKET_URL = "https://api.huobi.pro"
    TRADE_URL = "https://api.huobi.pro"

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        self.margin_accs = set()
        all_accounts = self.get_accounts()['data']
        for acc in all_accounts:
            acc_id = acc['id']
            if acc['type'] == 'spot':
                self.account_id = acc_id
            elif acc['type'] == 'margin':
                self.margin_accs.add(acc_id)

    def api_key_get(self, params, request_path):
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.api_key,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})

        host_url = self.TRADE_URL
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params['Signature'] = createSign(params, method, host_name, request_path, self.api_secret)

        url = host_url + request_path
        return http_get_request(url, params)

    def api_key_post(self, params, request_path):
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': self.api_key,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}

        host_url = self.TRADE_URL
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, self.api_secret)
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return http_post_request(url, params)

    def get_kline(self, symbol, period, size=150):
        """
        :param symbol
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        :param size: 可选值： [1,2000]
        :return:
        """
        params = {'symbol': symbol,
                  'period': period,
                  'size': size}

        url = self.MARKET_URL + '/market/history/kline'
        return http_get_request(url, params)


    # 获取marketdepth
    def get_depth(self, symbol, type):
        """
        :param symbol
        :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        params = {'symbol': symbol,
                  'type': type}

        url = self.MARKET_URL + '/market/depth'
        return http_get_request(url, params)

    # 获取tradedetail
    def get_trade(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = self.MARKET_URL + '/market/trade'
        return http_get_request(url, params)

    # 获取merge ticker
    def get_ticker(self, symbol):
        """
        :param symbol: 
        :return:
        """
        params = {'symbol': symbol}

        url = self.MARKET_URL + '/market/detail/merged'
        return http_get_request(url, params)

    # 获取 Market Detail 24小时成交量数据
    def get_detail(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = self.MARKET_URL + '/market/detail'
        return http_get_request(url, params)

    # 获取  支持的交易对
    def get_symbols(self, long_polling=None):
        """

        """
        params = {}
        if long_polling:
            params['long-polling'] = long_polling
        path = '/v1/common/symbols'
        return self.api_key_get(params, path)

    '''
    Trade/Account API
    '''

    def get_accounts(self):
        """
        :return: 
        """
        path = "/v1/account/accounts"
        params = {}
        return self.api_key_get(params, path)

    # 获取当前账户资产
    def _get_spot_balance(self):
        """
        :param acct_id
        :return:
        """
        url = "/v1/account/accounts/{0}/balance".format(self.account_id)
        params = {"account-id": self.account_id}
        return self.api_key_get(params, url)['data']['list']

    def _get_margin_balance(self):
        """
        :param acct_id
        :return:
        """
        balances = []
        for acc_id in self.margin_accs:
            url = "/v1/account/accounts/{0}/balance".format(acc_id)
            params = {"account-id": acc_id}
            balances.extend(self.api_key_get(params, url)['data']['list'])

        return balances

    def get_balance(self):
        balance = self._get_spot_balance()
        margin_bal = self._get_margin_balance()
        # pp.pprint(margin_bal)
        balance.extend(margin_bal)
        return balance


    # 下单

    # 创建并执行订单
    def send_order(self, amount, source, symbol, _type, price=0):
        """
        :param amount: 
        :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
        :param symbol: 
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price: 
        :return: 
        """
        try:
            accounts = self.get_accounts()
            acct_id = accounts['data'][0]['id']
        except BaseException as e:
            print ('get acct_id error.%s' % e)
            acct_id = ACCOUNT_ID

        params = {"account-id": acct_id,
                  "amount": amount,
                  "symbol": symbol,
                  "type": _type,
                  "source": source}
        if price:
            params["price"] = price

        url = '/v1/order/orders/place'
        return self.api_key_post(params, url)


    # 撤销订单
    def cancel_order(self, order_id):
        """
        
        :param order_id: 
        :return: 
        """
        params = {}
        url = "/v1/order/orders/{0}/submitcancel".format(order_id)
        return self.api_key_post(params, url)


    # 查询某个订单
    def order_info(self, order_id):
        """
        
        :param order_id: 
        :return: 
        """
        params = {}
        url = "/v1/order/orders/{0}".format(order_id)
        return self.api_key_get(params, url)


    # 查询某个订单的成交明细
    def order_matchresults(self, order_id):
        """
        
        :param order_id: 
        :return: 
        """
        params = {}
        url = "/v1/order/orders/{0}/matchresults".format(order_id)
        return self.api_key_get(params, url)


    # 查询当前委托、历史委托
    def orders_list(self, symbol, states, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        """
        
        :param symbol: 
        :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date: 
        :param end_date: 
        :param _from: 
        :param direct: 可选值{prev 向前，next 向后}
        :param size: 
        :return: 
        """
        params = {'symbol': symbol,
                  'states': states}

        if types:
            params[types] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        url = '/v1/order/orders'
        return self.api_key_get(params, url)


    # 查询当前成交、历史成交
    def orders_matchresults(self, symbol, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        """
        
        :param symbol: 
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date: 
        :param end_date: 
        :param _from: 
        :param direct: 可选值{prev 向前，next 向后}
        :param size: 
        :return: 
        """
        params = {'symbol': symbol}

        if types:
            params[types] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        url = '/v1/order/matchresults'
        return self.api_key_get(params, url)



    # 申请提现虚拟币
    def withdraw(self, address, amount, currency, fee=0, addr_tag=""):
        """

        :param address_id: 
        :param amount: 
        :param currency:btc, ltc, bcc, eth, etc ...(火币Pro支持的币种)
        :param fee: 
        :param addr-tag:
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {'address': address,
                  'amount': amount,
                  "currency": currency,
                  "fee": fee,
                  "addr-tag": addr_tag}
        url = '/v1/dw/withdraw/api/create'

        return self.api_key_post(params, url)

    # 申请取消提现虚拟币
    def cancel_withdraw(self, address_id):
        """

        :param address_id: 
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {}
        url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(address_id)

        return self.api_key_post(params, url)


    '''
    借贷API
    '''

    # 创建并执行借贷订单


    def send_margin_order(self, amount, source, symbol, _type, price=0):
        """
        :param amount: 
        :param source: 'margin-api'
        :param symbol: 
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price: 
        :return: 
        """
        try:
            accounts = self.get_accounts()
            acct_id = accounts['data'][0]['id']
        except BaseException as e:
            print ('get acct_id error.%s' % e)
            acct_id = ACCOUNT_ID

        params = {"account-id": acct_id,
                  "amount": amount,
                  "symbol": symbol,
                  "type": _type,
                  "source": 'margin-api'}
        if price:
            params["price"] = price

        url = '/v1/order/orders/place'
        return self.api_key_post(params, url)

    # 现货账户划入至借贷账户


    def exchange_to_margin(self, symbol, currency, amount):
        """
        :param amount: 
        :param currency: 
        :param symbol: 
        :return: 
        """
        params = {"symbol": symbol,
                  "currency": currency,
                  "amount": amount}

        url = "/v1/dw/transfer-in/margin"
        return self.api_key_post(params, url)

    # 借贷账户划出至现货账户


    def margin_to_exchange(self, symbol, currency, amount):
        """
        :param amount: 
        :param currency: 
        :param symbol: 
        :return: 
        """
        params = {"symbol": symbol,
                  "currency": currency,
                  "amount": amount}

        url = "/v1/dw/transfer-out/margin"
        return self.api_key_post(params, url)

    # 申请借贷
    def get_margin(self, symbol, currency, amount):
        """
        :param amount: 
        :param currency: 
        :param symbol: 
        :return: 
        """
        params = {"symbol": symbol,
                  "currency": currency,
                  "amount": amount}
        url = "/v1/margin/orders"
        return self.api_key_post(params, url)

    # 归还借贷
    def repay_margin(self, order_id, amount):
        """
        :param order_id: 
        :param amount: 
        :return: 
        """
        params = {"order-id": order_id,
                  "amount": amount}
        url = "/v1/margin/orders/{0}/repay".format(order_id)
        return self.api_key_post(params, url)

    # 借贷订单
    def loan_orders(self, symbol, currency, start_date="", end_date="", start="", direct="", size=""):
        """
        :param symbol: 
        :param currency: 
        :param direct: prev 向前，next 向后
        :return: 
        """
        params = {"symbol": symbol,
                  "currency": currency}
        if start_date:
            params["start-date"] = start_date
        if end_date:
            params["end-date"] = end_date
        if start:
            params["from"] = start
        if direct and direct in ["prev", "next"]:
            params["direct"] = direct
        if size:
            params["size"] = size
        url = "/v1/margin/loan-orders"
        return self.api_key_get(params, url)


    # 借贷账户详情,支持查询单个币种
    def margin_balance(self, symbol):
        """
        :param symbol: 
        :return: 
        """
        params = {}
        url = "/v1/margin/accounts/balance"
        if symbol:
            params['symbol'] = symbol
        
        return self.api_key_get(params, url)
