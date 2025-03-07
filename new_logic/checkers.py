from typing import List, Union

class Trade:
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
  
  def close(self):
    # closing the trade
    pass