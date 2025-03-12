import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from polygon import RESTClient
import pandas as pd
import datetime
from new_logic.config import settings
from typing import Union, Optional
from datetime import date, datetime, timedelta


class Service:
    def take_polygon_gold_historical_data(
            self, 
            from_: Union[str, int, datetime, date],
            to: Union[str, int, datetime, date],
            candle_size: int,
            limit: Optional[int] = None
) -> pd.DataFrame:
        client = RESTClient(api_key=settings.POLYGON_API_KEY)
        aggs = []
        for a in client.list_aggs(ticker="C:XAUUSD", multiplier=candle_size, timespan="minute", from_=from_, to=to, limit=limit):
            data = {
                "GmtTime": pd.to_datetime(a.timestamp, unit='ms', utc=True),
                "Open": a.open,
                "High": a.high,
                "Low": a.low,
                "Close": a.close,
                "Volume": a.volume
            }
            aggs.append(data)
        df = pd.DataFrame(aggs)
        return df
    
    def calculate_sell_price(self, pdLSH: float, adL: float) -> float:
        return adL + ((pdLSH - adL) * 0.764)

    def calculate_buy_price(self, pdLSL: float, adH: float) -> float:
        return adH - ((adH - pdLSL) * 0.764)

    def calculate_rr(self, entry_point, stop_loss, profit_target, trade_type="BUY"):
        if trade_type.upper() == "BUY":
            # For BUY: risk is entry - stop_loss, reward is profit_target - entry.
            risk = entry_point - stop_loss
            reward = profit_target - entry_point
        elif trade_type.upper() == "SELL":
            # For SELL: risk is stop_loss - entry, reward is entry - profit_target.
            risk = stop_loss - entry_point
            reward = entry_point - profit_target
        k = reward / risk
        return f"1:{round(k, 2)}"

    def calculate_half_fib_sell(self, pdLSH: float, adL: float) -> float:
        return adL + ((pdLSH - adL) * 0.5)

    def calculate_half_fib_buy(self, pdLSL: float, adH: float) -> float:
        return adH - ((adH - pdLSL) * 0.5)
    
    def find_pdLSH(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with previous day date.
            3. Returns None if previous date dataframe is empty.
            4. Returns Max value in "High" column of the previous date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.GmtTime)
        previous_day_date_datetime = candle_date_datetime - timedelta(days=1)
        previous_day_date_string = str(previous_day_date_datetime.date())
        filtered_df = data[data['GmtTime'].str.startswith(previous_day_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["High"].max()

    def find_pdLSL(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with previous day date.
            3. Returns None if previous date dataframe is empty.
            4. Returns Min value in "Low" column of the previous date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.GmtTime)
        previous_day_date_datetime = candle_date_datetime - timedelta(days=1)
        previous_day_date_string = str(previous_day_date_datetime.date())
        filtered_df = data[data['GmtTime'].str.startswith(previous_day_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["Low"].min()
    
    def find_adH(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with actual day date.
            3. Returns None if actual date dataframe is empty.
            4. Returns Max value in "High" column of the actual date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.GmtTime)
        candle_date_string = str(candle_date_datetime.date())
        filtered_df = data[data['GmtTime'].str.startswith(candle_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["High"].max()

    def find_adL(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with actual day date.
            3. Returns None if actual date dataframe is empty.
            4. Returns Min value in "Low" column of the actual date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.GmtTime)
        candle_date_string = str(candle_date_datetime.date())
        filtered_df = data[data['GmtTime'].str.startswith(candle_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["Low"].min()
    
    def get_datetime_from_iso_string(self, iso_string:str) -> datetime:
        return datetime.strptime(iso_string.split(" ")[0], "%Y-%m-%d")