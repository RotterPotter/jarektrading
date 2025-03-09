from typing import List, Union, Optional, Tuple, Dict
from abc import ABC, abstractmethod
import pydantic 
import pandas as pd
from service import Service
from datetime import time, datetime

class VariableRequired(Exception):
  def __init__(self, message):
    super().__init__(message)

class Checker:
  def __init__(self, active_checkers:List[str], data, params: dict):
    self.CHECKERS = {
      "end_time_checker": self.end_time_checker
    }
    self.REQUIRED_PARAMS = {
      "end_time_checker": ["end_time", ]
    }
    self.data = data
    self.params = params

    # removes not active checkers
    try:
      keys_to_delete = [checker_name for checker_name in self.CHECKERS.keys() if checker_name not in active_checkers]
      for key in keys_to_delete:
        del self.CHECKERS[key]
    except Exception as e:
      print(f"Error: {e}")

    # check if required params for checkers are passed. if not, raise ParamsRequired custom error
    try:
      for checker_name, param_list in self.REQUIRED_PARAMS.items():
        for param in param_list:
          if param not in params.keys():
            raise VariableRequired(f"Parameter {param} is required for checker {checker_name}.")
    except VariableRequired as e:
      print(f"Error: {e}")


  def check(self, candle_data) -> Tuple[Optional[str], list]: # returns an action to take (BUY/SELL/SKIP) and list of triggered checkers
    triggered_checkers = []
    for checker_name, checker in self.CHECKERS.items():
      # checker returns true if was triggered
      action = checker(candle_data)
      if action:
        triggered_checkers.append({checker_name: action})
    
    action = None
    # returns the first triggered action if any
    if len(triggered_checkers) > 0:
      action = [action for action in triggered_checkers[0].items()][0]
    return action, triggered_checkers

  def end_time_checker(self, candle_data) -> Optional[str]:
    end_time = datetime.strptime(self.params["end_time"], "%H:%M").time()
    candle_time = datetime.strptime(candle_data.GmtTime.split(" ")[1][:5], "%H:%M").time()
    if candle_time >= end_time:
      return "SKIP"
    return None
  
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
    self.opened_trade: Optional[Trade] = None,
    self.checker = checker
    
  def start(self): 
    for candle_data in self.historical_data.itertuples(index=False): # iteration through candles and their data
      if self.opened_trade:
        # Use checkers to analyze candle's data and trade's data. If any of them was triggered, triggered checkers list
        action, triggered_checkers = self.checker.check(candle_data) # takes candle data to check for triggeres, returns an action:str to take ("BUY"/"SELL"/"SKIP" or None) and list of triggered checkers
        # if there are trigered checkers, close the trade
        if len(triggered_checkers) > 0:
          self.close_trade()
      else:
        # Use checkers to analyze candle's data. If any of them was triggered, returns true
        action, triggered_checkers = self.checker.check(candle_data) # takes candle data to check for triggeres, returns an action:str to take ("BUY"/"SELL"/"SKIP" or None) and list of triggered checkers
        # if there are trigered checkers, close the trade
        if len(triggered_checkers) > 0:
          self.open_trade(candle_data, triggered_checkers)

  # TODO
  def open_trade(self, triggered_checkers):
    # Initialization of the Trade object and passing params
    trade = Trade() # TODO: define needed params
    # Set opened trade to this trade
    self.open_trade = trade
    # Add trade to executed trades variable
    self.executed_trades.append(trade)
    # Add logging of trade's opening
    self.add_log(f"{'-'*10}\nTrade was opened.\nTrade ID: {trade.id}.\nTriggered checkers {triggered_checkers}\nCandle time {candle_data.GmtTime}\n")

  def close_trade(self):
    pass
  
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
  # data.to_csv("data.csv", index=False)
  data = pd.read_csv("data.csv")
  checker = Checker(
    active_checkers=["end_time_checker",],
    data=data,
    params={"end_time": "23:00"}
  )
  program = BacktestingPorgram(historical_data=data, initial_balance=10000, checker=checker)
  program.start()

