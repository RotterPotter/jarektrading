from typing import List, Union, Optional, Tuple, Dict
from abc import ABC, abstractmethod
import pydantic 
import pandas as pd
from service import Service
from datetime import time, datetime
from checkers import Checker

class BacktestingPorgram:
  def __init__(
      self, 
      historical_data: pd.DataFrame,
      initial_balance: float,
      checker: Checker

  ):
    self.historical_data = historical_data
    self.balance = initial_balance
    self.executed_trades: List[Trade] = []
    self.logs = []
    self.opened_trade: Optional[Trade] = None
    self.checker = checker
    
  def start(self): 
    for candle_data in self.historical_data.itertuples(index=False): # iteration through candles and their data
      if not self.opened_trade is None:
        # Use checkers to analyze candle's data and trade's data. If any of them was triggered, triggered checkers list
        action, triggered_checkers = self.checker.check(candle_data, trade_is_opened=True) # takes candle data to check for triggeres, returns an action:str to take ("BUY"/"SELL"/"SKIP" or None) and list of triggered checkers
        # if there are trigered checkers, close the trade
        if len(triggered_checkers) > 0:
          pass
      else:
        # Use checkers to analyze candle's data. If any of them was triggered, returns true
        action, triggered_checkers = self.checker.check(candle_data, trade_is_opened=False) # takes candle data to check for triggeres, returns an action:str to take ("BUY"/"SELL"/"SKIP" or None) and list of triggered checkers
        # if there are trigered checkers, close the trade
        if len(triggered_checkers) > 0:
          pass

  # TODO
  def open_trade(self, triggered_checkers):
    print("Trade is opened")
    # # Initialization of the Trade object and passing params
    # trade = Trade() # TODO: define needed params
    # # Set opened trade to this trade
    # self.open_trade = trade
    # # Add trade to executed trades variable
    # self.executed_trades.append(trade)
    # # Add logging of trade's opening
    # self.add_log(f"{'-'*10}\nTrade was opened.\nTrade ID: {trade.id}.\nTriggered checkers {triggered_checkers}\nCandle time {candle_data.GmtTime}\n")

  def close_trade(self):
    print("Trade was closed")
  
  def add_log(self, message:str):
    self.logs.append(message)

  def check_to_close(self, candle_data) -> list:
    return []

  def check_to_open(self, candle_data) -> list:
    return []
  
class Trade(ABC):
  def __init__(
      self,
      trade_type:str, # SELL/BUY
      program: BacktestingPorgram,
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

if __name__ == "__main__":
  service = Service()
  # data = service.take_polygon_gold_historical_data(from_="2023-06-01", to="2023-06-13", candle_size=15)
  data = pd.read_csv("./jarektrading/new_logic/data.csv")
  checker = Checker(
    active_checkers={
      "when_trade_is_opened" : ["end_time_checker"],
      "when_trade_is_not_opened" : ["no_more_trades_time_checker"]
    },
    data=data,
    params={"end_time": "23:00", "no_more_trades_time": "21:30"}
  )
  program = BacktestingPorgram(historical_data=data, initial_balance=10000, checker=checker)
  program.start()

