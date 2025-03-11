import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from new_logic.checkers import Checker

import pandas as pd

def end_time_checker_test(data):
  checker = Checker(
    active_checkers=["end_time_checker",],
    data=data,
    params={"end_time": "00:30"}
  )

  results = []
  for candle_data in data[:5].itertuples():
    results.append(checker.end_time_checker(candle_data))
  if results == [None, None, 'CLOSE', 'CLOSE', 'CLOSE']:
    return "Success"
  else:
    return "Fail"

if __name__ == "__main__":
  import pandas as pd
  testing_data = pd.read_csv("jarektrading/tests/data.csv")
  print(end_time_checker_test(testing_data))