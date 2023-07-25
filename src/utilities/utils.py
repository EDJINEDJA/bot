import json
import time
from multiprocessing.pool import ThreadPool as Pool

import ccxt
import numpy as np
import pandas as pd
import ta
from tqdm import tqdm

from src.utilities.custom_indicators import SuperTrend


class utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def loadJson(file: str):
        assert type(file) == str, "issue in loadjson, please file must be in str format"
        f = open(
            file,
        )
        data = json.load(f)
        f.close()
        return data

    @staticmethod
    def get_data(binance, params_coin, config):
        # Get data
        df_list = {}
        for pair in params_coin:
            params = params_coin[pair]
            df = binance.get_last_historical(pair, config["timeframe"], 1000)

            # -- Populate indicators --
            super_trend = SuperTrend(
                df["high"],
                df["low"],
                df["close"],
                params["st_short_atr_window"],
                params["st_short_atr_multiplier"],
            )

            df["super_trend_direction"] = super_trend.super_trend_direction()
            df["ema_short"] = ta.trend.ema_indicator(
                close=df["close"], window=params["short_ema_window"]
            )
            df["ema_long"] = ta.trend.ema_indicator(
                close=df["close"], window=params["long_ema_window"]
            )

            df_list[pair] = df

        return df_list


class SpotBinance:
    def __init__(self, apiKey=None, secret=None):
        binance_auth_object = {
            "apiKey": apiKey,
            "secret": secret,
        }
        if binance_auth_object["secret"] is None:
            self._auth = False
            self._session = ccxt.binance()
        else:
            self._auth = True
            self._session = ccxt.binance(binance_auth_object)
        self.market = self._session.load_markets()

    @staticmethod
    def authentication_required(fn):
        """Annotation for methods that require auth."""

        def wrapped(self, *args, **kwargs):
            if not self._auth:
                print("You must be authenticated to use this method", fn)
                exit()
            else:
                return fn(self, *args, **kwargs)

        return wrapped

    def get_min_order_amount(self, symbol):
        return self._session.markets_by_id[symbol][0]["limits"]["amount"]["min"]

    def convert_amount_to_precision(self, symbol, amount):
        return float(self._session.amount_to_precision(symbol, amount))

    def convert_price_to_precision(self, symbol, price):
        return float(self._session.price_to_precision(symbol, price))

    def get_last_historical(self, symbol, timeframe, limit):
        result = pd.DataFrame(
            data=self._session.fetch_ohlcv(symbol, timeframe, None, limit=limit)
        )
        result = result.rename(
            columns={
                0: "timestamp",
                1: "open",
                2: "high",
                3: "low",
                4: "close",
                5: "volume",
            }
        )
        result = result.set_index(result["timestamp"])
        result.index = pd.to_datetime(result.index, unit="ms")
        del result["timestamp"]
        return result

    @authentication_required
    def get_open_order(self, symbol):
        try:
            return self._session.fetchOpenOrders(symbol)
        except BaseException as err:
            raise Exception("An error occured in get_open_order", err)

    @authentication_required
    def get_all_balance(self):
        return self._session.fetchBalance()["total"]

    @authentication_required
    def cancel_all_orders(self, symbol):
        return self._session.cancelAllOrders(symbol)

    @authentication_required
    def place_limit_order(self, pair, side, quantity, price):
        return self._session.createOrder(
            symbol=pair,
            type="limit",
            side=side,
            amount=quantity,
            price=price,
            params={},
        )
