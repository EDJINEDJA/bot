import os
import time
from datetime import datetime

from dotenv import load_dotenv

from src.strategies.strategy import Pilot
from src.utilities.utils import SpotBinance, utils

load_dotenv("./env/.env")

params_coin = utils.loadJson("./src/coins/param_coins.json")


def bot(config):

    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    print("--- Start Execution Time :", current_time, "---")

    binance = SpotBinance(
        apiKey=os.environ["apiKey"],
        secret=os.environ["secret"],
    )

    pair_list = params_coin.keys()
    symbol_list = [pair.replace("USDT", "") for pair in pair_list]

    df_list = utils.get_data(binance, params_coin, config)

    all_balance = binance.get_all_balance()

    symbol_balance = {}
    usdt_balance = all_balance["USDT"]
    usdt_all_balance = usdt_balance
    for k in all_balance:
        if k in symbol_list:
            if all_balance[k] > binance.get_min_order_amount(k + "USDT"):
                symbol_balance[k] = binance.convert_amount_to_precision(
                    k + "USDT", all_balance[k]
                )
                usdt_all_balance = (
                    usdt_all_balance
                    + symbol_balance[k] * df_list[k + "USDT"].iloc[-1]["close"]
                )
            else:
                symbol_balance[k] = 0
    print("symbol_balance", symbol_balance)
    print("usdt_all_balance", usdt_all_balance)

    for symbol in params_coin:
        try:
            binance.cancel_all_orders(symbol)
        except Exception as e:
            print(f"    Error: {e}")

        for symbol in symbol_balance:
            pair = symbol + "USDT"
            row = df_list[pair].iloc[-2]

            if symbol_balance[symbol] == 0:
                if Pilot.open_long(row):
                    buy_limit_price = binance.convert_price_to_precision(
                        pair, row["ema_short"]
                    )
                    buy_quantity_in_usd = (
                        usdt_all_balance * params_coin[pair]["wallet_exposure"]
                    )
                    buy_quantity = binance.convert_amount_to_precision(
                        pair, (buy_quantity_in_usd / buy_limit_price)
                    )
                    print(
                        f"Buy limit on {pair} of {buy_quantity} at the price of {buy_limit_price}$"
                    )
                    try:
                        print(buy_quantity_in_usd)
                        binance.place_limit_order(
                            pair, "Buy", buy_quantity, buy_limit_price
                        )
                    except Exception as e:
                        print(f"    Error: {e}")
            elif symbol_balance[symbol] > 0:
                if Pilot.close_long(row):
                    sell_limit_price = binance.convert_price_to_precision(
                        pair, row["ema_short"]
                    )
                    sell_quantity = binance.convert_amount_to_precision(
                        pair, symbol_balance[symbol]
                    )
                    print(
                        f"Sell limit on {pair} of {sell_quantity} at the price of {sell_limit_price}$"
                    )
                    try:
                        binance.place_limit_order(
                            pair, "Sell", sell_quantity, sell_limit_price
                        )
                    except Exception as e:
                        print(f"    Error: {e}")
