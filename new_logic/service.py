from polygon import RESTClient
import pandas as pd
import datetime
from config import settings
from typing import Union, Optional
from datetime import date, datetime


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
