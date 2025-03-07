from typing import List, Union, Optional
from abc import ABC, abstractmethod
import pydantic 
import pandas as pd
from service import Service


# Format to be outputed from the data extractors
class GeneralInputDataFormat(pydantic.BaseModel):
  pass

class DataExtractor(ABC):
  class NotImplementedError(Exception):
    pass
  
  @abstractmethod
  def extract_data(self, data_fp:str) :
    pass

class TestingDataExtractor(DataExtractor):
  def extract_data(self):
    return super().extract_data()

class Trade(ABC):
  def __init__(
      self,
      ticker:str,
      position_amount:float, 
      entry_level:float, # ?percantage from amount of the position / value
      take_profit_levels:List[float], # ?percantage or amount
      stop_loss:float # ?
    ):
    # opening the trade
    pass
  
  @abstractmethod
  def close(self):
    # closing the trade
    pass

class BacktestingPorgram:
  def __init__(
      self, 
      historical_data: pd.DataFrame,
      initial_balance: float,
  ):
    self.historical_data = historical_data
    self.balance = initial_balance
    self.executed_trades: List[Trade] = []
    self.debug_report = pd.DataFrame([], columns=[])
    self.logs = []
    self.opened_trade: Optional[Trade] = None

  def start(self): 
    for candle_data in self.historical_data.itertuples(index=False): # iteration through candles and their data
      if self.opened_trade:
        # Use checkers to analyze candle's data and trade's data. If any of them was triggered, triggered checkers list
        triggered_checkers: list = self.check_to_close(candle_data)
        # if there are trigered checkers, close the trade
        if len(triggered_checkers) > 0:
          self.close_the_trade(triggered_checkers)
      else:
        # Use checkers to analyze candle's data. If any of them was triggered, returns true
        triggered_checkers: list = self.check_to_open(candle_data)
        # if there are trigered checkers, close the trade
        if len(triggered_checkers) > 0:
          self.open_the_trade(triggered_checkers)

  def close_the_trade(self):
    pass

  def open_the_trade(self):
    pass

  def check_to_close(self, candle_data) -> bool:
    pass

  def check_to_open(self, candle_data) -> bool:
    pass

  def analyze_candle_data_and_make_decision(self, candle_data):
    # if self.opened_trade:
    #   if self.opened_trade. type == SELL:
    #     if self.opened_trade. trigered_checker_name == "bla bla":
    #       Functionality
    #   elif self.opened_trade.type == BUY:
    #        pass
    # else:
    #   self.check()
    pass

# How program execution will look like?

if __name__ == "__main__":
  service = Service()
  data = service.take_polygon_gold_historical_data(from_="2023-06-01", to="2023-06-13", candle_size=15)
  program = BacktestingPorgram(historical_data=data, initial_balance=10000)
  program.start()
  # report = program.generate_report()


