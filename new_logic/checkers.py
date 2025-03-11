import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from typing import List, Tuple, Optional, Dict
from datetime import datetime
from new_logic.service import Service

class VariableRequired(Exception):
  def __init__(self, message):
    super().__init__(message)

class Checker:
  def __init__(self, active_checkers:Dict[str, List[str]], data, params: dict):
    self.CHECKERS = {
      "end_time_checker": self.end_time_checker,
      "no_more_trades_time_checker": self.no_more_trades_time_checker,
      "to_sell_order_1_checker": self.to_sell_order_1_checker
    }
    
    self.REQUIRED_PARAMS = {
      "end_time_checker": ["end_time", ],
      "no_more_trades_time_checker" : ["no_more_trades_time",]
    }
    self.data = data
    self.params = params
    self.active_checkers = active_checkers

    # check if required params for checkers are passed. if not, raise ParamsRequired custom error
    try:
      for active_checker in self.active_checkers:
        if self.REQUIRED_PARAMS.get(active_checker, None) is None:
          continue
        required_params = self.REQUIRED_PARAMS[active_checker]
        for param in required_params:
          if not param in self.params.keys():
            raise VariableRequired(f"Parameter {param} is required for checker {active_checker}.")
    except VariableRequired as e:
      print(f"Error: {e}")

  def check(self, candle_data, trade_is_opened:bool) -> Tuple[Optional[str], list]: # returns an action to take (BUY/SELL/SKIP) and list of triggered checkers
    triggered_checkers = []
    for checker_name in self.CHECKERS.keys():
      if trade_is_opened:
        for checker_name in self.active_checkers["when_trade_is_opened"]:
          action = self.CHECKERS[checker_name](candle_data)
          if action is not None:
            triggered_checkers.append({checker_name: action})
      elif not trade_is_opened:
        for checker_name in self.active_checkers["when_trade_is_not_opened"]:
          action = self.CHECKERS[checker_name](candle_data)
          if action is not None:
            triggered_checkers.append({checker_name: action})

    
    action = None
    # returns the first triggered action if any
    if len(triggered_checkers) > 0:
      action = [action for action in triggered_checkers[0].items()][0]
    return action, triggered_checkers

  def end_time_checker(self, candle_data) -> Optional[str]:
    """
      Purpose: 
        To tell the program to CLOSE opened trade, if candle_time >= end_time (time when we should close all opened trades)
      Description:
        Returns "CLOSE" action if time variable of candle >= than time when we shouldn't open any trade (specified in Checker config)
        Returns "None" if not triggered. That means for a program that next checkers in the available list should be executed.
        "CLOSE" action means that program should close the trade.
    """
    end_time = datetime.strptime(self.params["end_time"], "%H:%M").time()
    candle_time = datetime.strptime(str(candle_data.GmtTime).split(" ")[1][:5], "%H:%M").time()
    if candle_time >= end_time:
      return "CLOSE"
    return None
  
  def no_more_trades_time_checker(self, candle_data) -> Optional[str]:
    """
      Purpose:
        To prevent opening new trades on current candle after no more trades time.
      Desctiption: 
        Check if candle time is >= than no_more_trades_time (specified in checker config). If so, returns "SKIP" action.
        "SKIP" action means, that no more checkers should be checked for this candle.
        Returns None if checker wasn't triggered ( in this case, if candle_time < no_more_trades_time).
        None tells to the program to go through the next available checker.

    """
    candle_time = datetime.strptime(str(candle_data.GmtTime).split(" ")[1][:5], "%H:%M").time()
    no_more_trades_time = datetime.strptime(self.params["no_more_trades_time"], "%H:%M").time()
    if candle_time >= no_more_trades_time:
      return "SKIP"
    return None

  # TODO test for the checker
  def to_sell_order_1_checker(self, candle_data):
    """
      Purpose:
        To check candle's conditions to open sell trade. (candle_data.High >= sell_price)
      Desctiption: 
        1. Uses custom functions from the service.Service object to find required variables (pdLSH, adL) for the step 3.
        2. If required variables for step 3 weren't found (in case of data missing), returns None.
        3. Calculates sell price using custom function from the service.Service object.
        4. Returns "SELL" action, if candle_data.High >= sell_price.
        5. Returns None, if candle_data.High < sell_price.
      Notes:
        None tells to the program to move to the next checker.
        "SELL" tells to the program to execute sell trade.
    """
    service = Service()
    pdLSH = service.find_pdLSH(candle_data, self.data) # previous day london session's low
    adL = service.find_adL(candle_data, self.data) # actual day low

    if pdLSH is None or adL is None:
      return None
    
    sell_price = service.calculate_sell_price(pdLSH, adL)
    if candle_data.High >= sell_price:
      return "SELL"
    return None

  # TODO checker + test
  def to_buy_order_1_checker(self, candle_date):
    pass

  # TODO checker + test
  def if_sell_was_closed_checker(self, candle_data):
    pass

  # TODO checker + test
  def if_buy_was_closed_checker(self, candle_data):
    pass

  # TODO CLOSING TRADES CHECKERS ( FOR BUY AND FOR SELL)

