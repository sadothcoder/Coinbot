import pprint as pp
import sys
import time
import os

from coinbot import Coinbot


def p(x):
    pp.pprint(x)


def run(bot):
    VALID_COMMANDS = {
        'balance',  # check balance of an exchange | balance [exchange]
        'coins',    # check coins of an exchange | coins [exchange]
        'price',    # check price of a pair in an exchange | price [coin] [base] [exchange]
        'diff',    # check price diff
    }
    while(True):
        _input = input(">> ")

        if _input in {'q', 'quit'}:
            print('EOSGOGO!!')
            exit(0)

        _inputs = _input.split(' ')

        if (len(_inputs) == 2):
            command, exchange = _inputs[0], _inputs[1]
        elif (len(_inputs) == 4):
            command, coin, base, exchange = _inputs[0], _inputs[1], _inputs[2], _inputs[3]

        if command == 'balance':
            p(bot.all_exchanges[exchange].get_full_balance())
        elif command == 'coins':
            p(bot.all_exchanges[exchange].coins)
        elif command == 'price':
            p(bot.all_exchanges[exchange].get_price(coin, base))
        else:
            print('This command has some problem! Re-enter!')


def check_ae_in_huobi(ex):
    while True:
        all_coins = ex.get_all_trading_coins()
        if 'ae' in all_coins:
            while True:
                os.system("osascript -e \'display notification \"AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!AE!\" \'")
                time.sleep(5)
            # print('*' * 10000)
        else:
            print('not yet')

        time.sleep(60)


if __name__ == '__main__':
    bot = Coinbot()
    if len(sys.argv) == 1:
        bot.get_full_balance(full=False)
    elif sys.argv[1] == 'full':
        bot.get_full_balance(full=True, allow_zero=False)
        # pp.pprint(bot.huobi.coins)
    elif sys.argv[1] == 'diff':
        bot.get_all_diff_rate(min_diff=0.001)
    elif sys.argv[1] == 'coins':
        bot.get_all_coin_balance()
    elif sys.argv[1] == 'test':
        check_ae_in_huobi(bot.all_exchanges['huobi'])
    elif sys.argv[1] == 'run':
        run(bot)
    else:
        print('nothing to do...')
