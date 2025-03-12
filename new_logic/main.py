import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

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
      checker: Checker

  ):
    self.historical_data = historical_data
    self.executed_trades: Dict[int, Trade] = {}
    self.checker_logger = pd.DataFrame([], columns=["CandleTime", "TriggeredChecker", "TakenAction"], )
    self.checker = checker
    self.summary = None
    self.opened_trade = None
    
  def start(self): 
    for candle_data in self.historical_data.itertuples(index=False): # iteration through candles and their data
      trade_is_opened = False if self.opened_trade is None else True # check if any trade is currently opened
      action, triggered_checker_name = self.checker.check(candle_data, trade_is_opened=trade_is_opened)  # uses all active checkers to check candle data
      
      # loggs an action and triggered_checker_name, candle gmt
      self.checker_log(candle_data.GmtTime, action, triggered_checker_name)

      if action in ["SKIP", None]:
        continue

      if action.split(" ")[0] in ["SELL", "BUY"]:
        position_in_percantage = float(action.split(" ")[1][:-1])
        #  initializes Trade object, adds trade to a self.opened_trade
        self.open_trade(trade_type=action, candle_data=candle_data, position_in_percantage=position_in_percantage, opening_checker_name=triggered_checker_name)
    
      elif action.startswith("CLOSE"):
        part_to_close = float(action.split(" ")[1][:-1])
        
        if part_to_close == 100:
          self.close_trade(candle_data=candle_data, triggered_checker=triggered_checker_name)
        else:
          self.close_trade_part(candle_data=candle_data, triggered_checker=triggered_checker_name, part=part_to_close)

      self.summary = self.generate_summary()

  def open_trade(self, trade_type:str, candle_data, position_in_percantage:float, opening_checker_name:str):
    new_trade = Trade(trade_type=trade_type, candle_data=candle_data, position_in_percantage=position_in_percantage, triggered_opening_checker=opening_checker_name)
    self.opened_trade = new_trade

  def close_trade(self, candle_data, triggered_checker:str):
    self.opened_trade.close(candle_data=candle_data, triggered_checker=triggered_checker)
    # add trade into executed trades
    self.executed_trades[self.opened_trade.id] = self.opened_trade
    self.opened_trade = None

  def close_trade_part(self, candle_data, triggered_checker, part:float):
    # this funciton returns True if trade was closed completely, False otherwise
    trade_was_closed = self.opened_trade.close_part(candle_data=candle_data, triggered_checker=triggered_checker, part_amount_perctage=part)
    if trade_was_closed:
      self.executed_trades[self.opened_trade.id] = self.opened_trade
      self.opened_trade = None

  def checker_log(self, candle_gmt, action:Optional[str], triggered_checker_name:Optional[str]):
    new_data = pd.DataFrame([[candle_gmt, triggered_checker_name, action]], columns=["CandleTime", "TriggeredChecker", "TakenAction"])
    self.checker_logger = pd.concat([self.checker_logger, new_data], ignore_index=True)

  # TODO
  def generate_summary(self) -> pd.DataFrame:
    data = {
    "Opened Trades": [self.calculate_opened_trades()],
    "Win Ratio": [self.calculate_win_ratio()],
    "Win Ratio excl.BE": [self.calculate_win_ratio_excl_be()],
    "Average R:R": [self.calculate_average_rr()],
    "P/L": [self.calculate_pl()],
    "Max Drop Down": [self.calculate_max_drop_down()],
    "Consecutive Losses": [self.calculate_consecutive_losses()],
    "Losses Quantity": [self.calculate_losses_quantity()],
    "BE Quantity": [self.calculate_be_quantity()],
    "Win Quantity": [self.calculate_win_quanity()]
    }
    return pd.DataFrame(data)
  
  # TODO
  def calculate_opened_trades(self):
    return None

  # TODO
  def calculate_win_ratio(self):
    return None

  # TODO
  def calculate_win_ratio_excl_be(self):
    return None

  # TODO
  def calculate_pl(self):
    return None

  # TODO
  def calculate_average_rr(self):
    return None
  
  # TODO
  def calculate_max_drop_down(self):
    return None

  # TODO
  def calculate_consecutive_losses(self):
    return None

  # TODO
  def calculate_losses_quantity(self):
    return None

  # TODO
  def calculate_be_quantity(self):
    return None

  # TODO
  def calculate_win_quanity(self):
    return None

  
  def print_executed_trades(self):
    for key, value in self.executed_trades.items():
      print(f'ID: {key} | {str(value)}')

class Trade():
  _id_counter = 0

  def __init__(
      self,
      trade_type: str, # SELL/BUY
      position_in_percantage:float, # part of the balance that we are risking
      triggered_opening_checker,
      candle_data,
    ):
    Trade._id_counter += 1
    self.id = Trade._id_counter
    self.opening_gmt_time = candle_data.GmtTime
    self.closing_gmt_time = None
    self.trade_type = trade_type
    self.entering_price = candle_data.Close

    self.position_in_percantage:float = position_in_percantage
    self.active_part = 100
    self.result = None
    self.pl = None
    self.logs = pd.DataFrame([], columns=["GmtTime", "Log"])
    self.triggered_opening_checker = triggered_opening_checker
    
    # logging of the trade opening
    self.log(self.opening_gmt_time, f"Trade {self.trade_type} was opened on the price {self.entering_price}.\nAction triggered by checker: {self.triggered_opening_checker}.")

  def log(self, gmt_time:str, message:str):
    new_data = pd.DataFrame([[gmt_time, message]], columns=["GmtTime", "Log"])
    self.logs = pd.concat([self.logs, new_data], ignore_index=True)
  
  def close(self, candle_data, triggered_checker):
    # on close should calculate parameters that will be used in summary. (result, pl,)
    if self.trade_type.startswith("SELL"):
      if self.entering_price > candle_data.Close:
          self.result = "WIN"  
      elif self.entering_price < candle_data.Close:
          self.result = "LOSS"  
      elif self.entering_price == candle_data.Close:
          self.result = "BE"  
    elif self.trade_type.startswith("BUY"):
      if self.entering_price < candle_data.Close:
          self.result = "WIN"  
      elif self.entering_price > candle_data.Close:
          self.result = "LOSS"  
      elif self.entering_price == candle_data.Close:
          self.result = "BE"
    self.closing_gmt_time = candle_data.GmtTime
    self.pl = -self.position_in_percantage if self.result == "LOSS" else self.position_in_percantage
    self.log(candle_data.GmtTime, f"Trade {self.trade_type} was closed on the price {candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nResult: {self.result}\nP/L: {self.pl}%.")
    

  def close_part(self, candle_data, part_amount_perctage:float, triggered_checker: Optional[str] = None) -> bool:
    if (self.active_part - part_amount_perctage) < 0:
      self.active_part = 0
      self.log(candle_data.GmtTime, f"Trade was partially closed on the price{candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nClosed by: {part_amount_perctage}%.\nRemaining position part: {self.active_part}%.\nInitializing closing trade process...")
      self.close(candle_data=candle_data)
      return True
    else:
      self.active_part -= part_amount_perctage
      self.log(candle_data.GmtTime, f"Trade was partially closed on the price{candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nClosed by: {part_amount_perctage}%.\nRemaining position part: {self.active_part}%.")
      return False
  
  def __str__(self):
    return f'{self.trade_type} trade ({self.opening_gmt_time}) - ({self.closing_gmt_time})'
    
if __name__ == "__main__":
  service = Service()
  # data = service.take_polygon_gold_historical_data(from_="2023-06-01", to="2023-06-13", candle_size=15)
  data = pd.read_csv("/home/iron/trading/jarektrading/new_logic/data.csv")
  
  checker = Checker(
    active_checkers={
      "when_trade_is_opened" : [
        "end_time_checker"
      ],
      "when_trade_is_not_opened" : [
        "start_time_checker",
        "no_more_trades_time_checker",
        "to_sell_order_1_checker",
        "to_buy_order_1_checker"
      ]
    },
    data=data,
    params={"start_time": "06:00", "end_time": "23:00", "no_more_trades_time": "21:30"}
  )

  program = BacktestingPorgram(historical_data=data, checker=checker)
  program.start()
  with open('logs.csv', 'w') as fp:
    program.checker_logger.to_csv(fp)
  program.print_executed_trades()
  print(program.summary)

