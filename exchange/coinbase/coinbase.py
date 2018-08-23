#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import hmac
import hashlib
import base64
from requests.auth import AuthBase

from ..exchange import Exchange


class Coinbase(Exchange):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_base_url = 'https://api.gdax.com/'
        self.auth = CoinbaseAuth(api_key, secret_key, passphrase)
        super().__init__('coinbase')
        self.connect_success()

    def get_pair(self, coin, base):
        return '%s-%s' % (coin, base)

    def get_BTC_price(self):
        return self.get_price('BTC', base='USD')

    def get_price(self, coin, base='BTC', _type=0):
        TYPES = {0: 'bids', 1: 'asks'}
        if coin not in {'BTC', 'ETH', 'BCH', 'LTC'}:
            raise Exception('this coin (%s) is not in GDAX!' % coin)

        pair = self.get_pair(coin, base)
        api_url = self.api_base_url + 'products/%s/book?level=1' % pair
        return float(requests.get(api_url, auth=self.auth).json()[TYPES[_type]][0][0])

    def get_full_balance(self, allow_zero=False):
        account = requests.get(self.api_base_url + 'accounts', auth=self.auth).json()

        BTC_price = self.get_BTC_price()
        coins = {
            'total': {'BTC': 0, 'USD': 0, 'num': 0},
            'USD': {'BTC': 0, 'USD': 0, 'num': 0}
        }
        for acc in account:
            coinName = acc['currency']
            num = float(acc['balance'])
            if allow_zero or num > 0:
                if coinName == 'USD':
                    USD_value = num
                else:
                    USD_value = self.get_price(coinName, base='USD') * num
                BTC_value = USD_value / BTC_price

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
        account = requests.get(self.api_base_url + 'accounts', auth=self.auth).json()
        coins = {}
        for acc in account:
            coinName = acc['currency']
            num = float(acc['balance'])
            if allow_zero or num > 0:
                coins[coinName] = num
        return coins


class CoinbaseAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(requests.get('https://api.gdax.com/time').json()['epoch'])
        message = (timestamp + request.method + request.path_url + (request.body or '')).encode('ascii')
        hmac_key = (base64.b64decode(self.secret_key))
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8').rstrip('\n')

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request











