class Exchange:
    def __init__(self, name):
        self.name = name
        self.market_bases = {'BTC', 'ETH', 'USDT'}
        self.coins = self.get_all_coin_balance()
        self.dontTouch = {'XRP', 'XEM', 'BTC', 'DOGE', 'SC', 'NEO', 'ZEC', 'BTG', 'MONA', 'WINGS', 'USDT', 'IOTA', 'EOS', 'QTUM', 'ADA', 'XLM', 'LSK', 'BTS', 'XMR', 'DASH', 'SNT', 'BCC', 'BCH', 'SBTC', 'BCX', 'ETF', 'LTC', 'ETH', 'BNB', 'ADA', 'BTS', 'SNT'}

    def connect_success(self):
        print('connected %s' % self.name)

    def get_pair(self, coin, base):
        # return the specific pair format for this exchange
        raise NotImplementedError("Please Implement this method")

    def get_all_trading_pairs(self):
        '''
        get all possible traing pairs in the form
        {
            'bases': {'BTC', 'ETH', etc...},
            'pairs': {
                'BTC': { ... },
                'ETH': { ... },
                ......
            }
            'all_pairs': { ... },
        }
        '''
        raise NotImplementedError("Please Implement this method")

    def get_all_trading_coins(self):
        '''
        get all possible traing coins in the form
        {'eos, neo, ...'}
        '''
        raise NotImplementedError("Please Implement this method")

    def get_my_pair(self, coin, base):
        # return my format
        return '%s-%s' % (coin, base)

    def get_BTC_price(self):
        raise NotImplementedError("Please Implement this method")

    def get_price(self, coin, base='BTC'):
        raise NotImplementedError("Please Implement this method")

    def get_full_balance(self, allow_zero=False):
        '''
        return format {
            'total': {
                'BTC': BTC_value,
                'USD': USD_value,
                'num': coin_num
            },
            'USD': { ... },
            coinName1: { ... },
            coinName2: { ... },
            ...
        }
        '''
        raise NotImplementedError("Please Implement this method")

    def get_all_coin_balance(self, allow_zero=False):
        '''
        return format {
            coinName1: num1,
            coinName2: num2,
            ...
        }
        '''
        raise NotImplementedError("Please Implement this method")

    def get_trading_pairs(self):
        '''
        return format: {
            'BTC': {'ADA', 'BAT', 'BTG', ...},
            'ETH': {'BAT', 'BNT', 'DNT', 'ETC', ...},
            'USDT': {'NEO', 'BTC', 'LTC', ...}
            ...
        }
        '''
        raise NotImplementedError("Please Implement this method")

    def get_market(self, coin, base):
        raise NotImplementedError("Please Implement this method")

    def get_coin_balance(self, coin):
        if coin in self.coins.keys():
            return self.coins[coin]
        else:
            return 0

    def get_order(self, id):
        raise NotImplementedError("Please Implement this method")

    # ----------- might need to update self.coins after buy/sell ----------- #
    def market_buy(self, coin, base='BTC', quantity=0):
        '''
        return format {
            'exchange': [exchange name],
            'side': [buy or sell],
            'pair': [coin-base],
            'price': [average filled price],
            'quantity': [filled quantity],
            'total': [total order value in BTC],
            'fee': [fee in BTC],
            'id': order id,
            'id2': customed order id
        }
        '''
        raise NotImplementedError("Please Implement this method")

    def market_sell(self, coin, base='BTC', quantity=0):
        raise NotImplementedError("Please Implement this method")

    def market_sell_all(self, coin, base='BTC'):
        quantity = self.get_coin_balance(coin)
        if quantity <= 0:
            print('%s does not have enough balance to sell' % coin)
            return None
        else:
            return self.market_sell(coin, base=base, quantity=quantity)

    def market_buy_everything(self, USD_price):
        raise NotImplementedError("Please Implement this method")

    def market_sell_everything(self):
        res = []
        for coin, num in self.coins.items():
            if coin not in self.dontTouch:
                response = self.market_sell_all(coin)
                res.append(response)
                print (response)
        return res







