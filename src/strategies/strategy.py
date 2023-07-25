class Pilot:
    def __init__(self) -> None:
        pass

    @staticmethod
    def open_long(row):
        return row["ema_short"] > row["ema_long"] and row["super_trend_direction"]

    @staticmethod
    def close_long(row):
        return row["ema_short"] < row["ema_long"] or not row["super_trend_direction"]
