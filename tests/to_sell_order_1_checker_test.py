import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from new_logic.checkers import Checker
from new_logic.service import Service

import pandas as pd

# TODO
def to_sell_order_1_checker_test(data):
  checker = Checker(
    active_checkers=["to_sell_order_1_checker",],
    data=data,
    params={}
  )

  results = []
  
  if results == [None, None, 'SKIP', 'SKIP', 'SKIP']:
    return "Success"
  else:
    return "Fail"

if __name__ == "__main__":
  import pandas as pd
  testing_data = pd.read_csv("jarektrading/tests/data.csv")
  print(to_sell_order_1_checker_test(testing_data))