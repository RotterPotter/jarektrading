from datetime import time, timedelta
import pandas as pd


class Service:
    # added Sunday just in case we will test crypto markets which are opened 24/7
    WEEKDAYS = ["Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self, start_time: time, end_time: time, no_more_trades_time: time, london_session_start_time: time, london_session_end_time: time):
        self.START_TIME = start_time
        self.NO_MORE_TRADES_TIME = no_more_trades_time
        self.END_TIME = end_time

        self.LONDON_SESSION_START_TIME = london_session_start_time
        self.LONDON_SESSION_END_TIME = london_session_end_time

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

    # def calculate_pl_buy(self, rr, trade_closing, stop_loss, buy_price,  closed_by_time_condition=False)

    # Oleksandr updated 08/02  !!!

    def generate_summary(self, report_df) -> pd.DataFrame:
        opened_trades_df = report_df[report_df["Name"] == "OPENING"]
        opened_trades_count = len(opened_trades_df)
        closed_trades_df = report_df[report_df["Name"] == "CLOSING"]
        closed_trades_count = len(closed_trades_df)
        if closed_trades_count == 0:
            win_ratio = 0
        else:
            win_ratio = (len(
                closed_trades_df[closed_trades_df["Result"] == "WIN"]) / closed_trades_count) * 100
        n = 0
        rr_sum = 0
        for row in opened_trades_df.itertuples(index=False):
            rr_sum += float(row._6.split(":")[1])
            n += 1
        average_rr = None if n == 0 else rr_sum / n
        max_drop_down = None
        capital = 1
        pl = 0
        consecutive_losses = 0
        # suggestion new vatriable max_consecutive_losses:
        max_consecutive_losses = 0


        for trade_row in closed_trades_df.itertuples(index=False):
            pl += float(trade_row._8)
            if trade_row.Result == "LOSS":
                consecutive_losses += 1
            elif trade_row.Result == "WIN" or "BE":
                if consecutive_losses > max_consecutive_losses:
                    max_consecutive_losses = consecutive_losses
                consecutive_losses = 0

        losses_quantity = len(
            closed_trades_df[closed_trades_df["Result"] == "LOSS"])
        be_quantity = len(closed_trades_df[closed_trades_df["Result"] == "BE"])
        win_quantity = len(
            closed_trades_df[closed_trades_df["Result"] == "WIN"])

        win_ratio_excl = win_quantity / (opened_trades_count - be_quantity) * 100
        # Win Quantity / (Opened Trades - BE Quantity)

        columns = ["Opened Trades", "Win Ratio","Win Ratio excl.BE",  "P/L", "Average R:R", "Max Drop Down",
                   "Consecutive Losses", "Losses Quantity", "BE Quantity", "Win Quantity"]
        return pd.DataFrame([[opened_trades_count, win_ratio,win_ratio_excl, pl, average_rr, max_drop_down, max_consecutive_losses, losses_quantity, be_quantity, win_quantity]], columns=columns)

    def backtest(self, start_date, end_date, file_path, debug=False):
        df = pd.read_csv(file_path, sep=';', parse_dates=['Date'])

        # Define report dataframe structure
        report_columns = ["Name", "Date", "Weekday", "Time", "Type", "Asset", "R:R", "Result", "P/L", "pdLSH", "pdLSL",
                          "adH", "adL", "Sell price", "Buy price", "Stop loss", "Take profit", "Candle High", "Candle Low", "Candle Close"]
        report_df = pd.DataFrame(columns=report_columns)

        # Convert to datetime
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        hero_date = start_datetime

        # Loop through dates
        while hero_date <= end_datetime:
            active_order = None

            # Filter for the current date
            hero_date_df = df[df['Date'].dt.date == hero_date.date()].copy()
            hero_date_df["Time"] = hero_date_df["Date"].dt.time  # Extract time

            # Previous day London session data
            pd_datetime = hero_date - timedelta(days=1)
            previous_day_df = df[df['Date'].dt.date ==
                                 pd_datetime.date()].copy()
            previous_day_df["Time"] = previous_day_df["Date"].dt.time

            pdls_df = previous_day_df[(previous_day_df["Time"] >= self.LONDON_SESSION_START_TIME) &
                                      (previous_day_df["Time"] <= self.LONDON_SESSION_END_TIME)]

            # Oleksandr updated 11/02
            n = 2
            while pdls_df.empty:
                pd_datetime = hero_date - timedelta(days=n)
                previous_day_df = df[df['Date'].dt.date ==
                                     pd_datetime.date()].copy()
                previous_day_df["Time"] = previous_day_df["Date"].dt.time

                pdls_df = previous_day_df[(previous_day_df["Time"] >= self.LONDON_SESSION_START_TIME) &
                                          (previous_day_df["Time"] <= self.LONDON_SESSION_END_TIME)]
                n += 1

            # Extract previous day's London session high and low
            pdLSH: float = pdls_df["High"].max()
            pdLSL: float = pdls_df["Low"].min()

            # Extract actual day's high/low before 6 AM
            hero_date_df_before_start = hero_date_df[hero_date_df["Time"]
                                                     <= self.START_TIME]
            adH: float = hero_date_df_before_start["High"].max()
            adL: float = hero_date_df_before_start["Low"].min()

            sell_price = buy_price = half_fib_sell = half_fib_buy = None
            stop_loss = take_profit = risk = reward = reward_to_risk = None

            # Oleksandr updated 08/02  !!!
            sell_was_closed = False
            buy_was_closed = False

            # Oleksandr updated 08/02  !!!
            sell_price_was_calculated_once = False
            buy_price_was_calculated_once = False

            stop_loss_is_sell_price = False
            stop_loss_is_buy_price = False

            stop_loss_on_trade_opening = None
            # Iterate through candles
            for candle_data in hero_date_df.itertuples(index=False):

                candle_time = candle_data.Time

                # Oleksandr updated 08/02  !!!
                if candle_time > self.NO_MORE_TRADES_TIME and active_order is None:
                    break

                # Oleksandr updated 08/02  !!!
                if candle_time < self.START_TIME:
                    continue

                # Update actual day high/low
                adH = max(adH, candle_data.High)
                adL = min(adL, candle_data.Low)

                # Oleksandr updated 08/02  !!!
                # Calculate or update potential trade levels ( if not after NO_MORE_TRADES time)
                if not candle_time >= self.NO_MORE_TRADES_TIME:
                    # Calculate potential trade levels
                    if pdLSH > adL and pdLSH > adH:
                        # Oleksandr updated 08/02  !!!
                        if not sell_was_closed:
                            # Oleksandr updated 08/02  !!!
                            if not sell_price_was_calculated_once:
                                sell_price_was_calculated_once = True
                            else:
                                sell_price = self.calculate_sell_price(
                                    pdLSH, adL)
                    # elif pdLSL < adH and pdLSL < adL:-------------------------------------------------------------------------
                    if pdLSL < adH and pdLSL < adL:
                        # Oleksandr updated 08/02  !!!
                        if not buy_was_closed:
                            # Oleksandr updated 08/02  !!!
                            if not buy_price_was_calculated_once:
                                buy_price_was_calculated_once = True
                            else:
                                buy_price = self.calculate_buy_price(
                                    pdLSL, adH)

                if debug:
                    new_data = pd.DataFrame([["DEBUG", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "None", "XAUUSD", reward_to_risk, "None", "None", pdLSH,
                                            pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                    report_df = pd.concat([report_df, new_data], ignore_index=True)
                # took above line out in order to see the rapor_df only with trades opened and closed , without the "DEBUG" lines. To make my analizing easier

                if active_order == "SELL":
                    half_fib_sell = self.calculate_half_fib_sell(pdLSH, adL)
                    # print(f"!Date: {hero_date.date()}, Time: {candle_time}, Candle_Low: {candle_data.Low} Fib_Sell: {half_fib_sell}, Fib_Buy: {calculate_half_fib_buy(pdLSL, adH)}\n\n")
                    # Set StopLoss to SellPrice if price reached 50%fib - Oleksandr updated 09/02  !!!

                    if candle_time >= self.END_TIME:
                        # Oleksandr updated 08/02  !!!
                        # Define result, calculate P/L
                        result = "WIN" if candle_data.Close <= sell_price else "LOSS"
                        # pl = f"+{reward_to_risk.split(':')[1]}" if result == "WIN" else f"-{reward_to_risk.split(':')[1]}"

                        pl = (sell_price - candle_data.Close) / (stop_loss_on_trade_opening - sell_price)
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, active_order, "XAUUSD", reward_to_risk, result, pl,
                                                pdLSH, pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        break

                    if candle_data.Low <= half_fib_sell:
                        # print("UPDATING!!!!!!!-----------------------")
                        stop_loss = sell_price
                        stop_loss_is_sell_price = True


                    if candle_data.High >= stop_loss and stop_loss_is_sell_price == True:
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "SELL", "XAUUSD", reward_to_risk, "BE", "0", pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        active_order = None
                        # Oleksandr updated 08/02  !!!
                        sell_price = None
                        # Oleksandr updated 09/02  !!!
                        sell_was_closed = True
                        stop_loss_is_sell_price = False

                    elif candle_data.High >= stop_loss and stop_loss_is_sell_price == False and stop_loss > sell_price:
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "SELL", "XAUUSD", reward_to_risk, "LOSS", "-1", pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)

                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        active_order = None
                        # Oleksandr updated 08/02  !!!
                        sell_price = None
                        # Oleksandr updated 09/02  !!!
                        sell_was_closed = True
                        stop_loss_is_sell_price = False

                    elif candle_data.Low <= take_profit:
                        pl = f"+{reward_to_risk.split(':')[1]}"
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "SELL", "XAUUSD", reward_to_risk, "WIN", pl, pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        active_order = None
                        # Oleksandr updated 08/02  !!!
                        sell_price = None
                        # Oleksandr updated 09/02  !!!
                        sell_was_closed = True
                        stop_loss_is_sell_price = False



                elif active_order == "BUY":
                    # Set StopLoss to BuyPrice if price reached 50%fib - Oleksandr updated 09/02  !!!
                    if candle_time >= self.END_TIME:
                        # Oleksandr updated 08/02  !!!
                        # Define result, calculate P/L
                        result = "WIN" if candle_data.Close >= buy_price else "LOSS"
                        pl = (candle_data.Close - buy_price) / (buy_price - stop_loss_on_trade_opening)

                        pl = f"+{round(pl,2)}" if result == "WIN" else f"-{round(pl,2)}"

                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, active_order, "XAUUSD", reward_to_risk, result, pl,
                                                pdLSH, pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        break

                    if candle_data.High >= self.calculate_half_fib_buy(pdLSL, adH):
                        stop_loss = buy_price
                        stop_loss_is_buy_price = True

                    # if candle_data.High >= stop_loss and stop_loss == sell_price:
                    # my suggestion of code
                    if candle_data.Low <= stop_loss and stop_loss_is_buy_price == True:
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "BUY", "XAUUSD", reward_to_risk, "BE", "0", pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)

                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        active_order = None
                        # Oleksandr updated 08/02  !!!
                        buy_price = None
                        # Oleksandr updated 09/02  !!!
                        buy_was_closed = True
                        stop_loss_is_buy_price = False

                    elif candle_data.Low <= stop_loss and stop_loss_is_buy_price == False and stop_loss < buy_price:
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "BUY", "XAUUSD", reward_to_risk, "LOSS", "-1", pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)

                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        active_order = None
                        # Oleksandr updated 08/02  !!!
                        buy_price = None
                        # Oleksandr updated 09/02  !!!
                        buy_was_closed = True
                        stop_loss_is_buy_price = False

                    elif candle_data.High >= take_profit:
                        pl = f"+{reward_to_risk.split(':')[1]}"
                        new_data = pd.DataFrame([["CLOSING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "BUY", "XAUUSD", reward_to_risk, "WIN", pl, pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                        active_order = None
                        # Oleksandr updated 08/02  !!!
                        buy_price = None
                        # Oleksandr updated 09/02  !!!
                        byt_was_closed = True
                        stop_loss_is_buy_price = False



                # Execute trade
                elif active_order is None:
                    # Oleksandr updated 08/02  !!!
                    if candle_time >= self.END_TIME:
                        break
                    # Oleksandr updated 08/02  !!!
                    if self.NO_MORE_TRADES_TIME <= candle_time and candle_time < self.END_TIME:
                        sell_price = None
                        buy_price = None
                        continue
                    elif sell_price and candle_data.High >= sell_price:
                        # Oleksandr updated 08/02  !!!
                        if sell_was_closed:
                            continue

                        active_order = "SELL"
                        stop_loss = pdLSH
                        stop_loss_on_trade_opening = stop_loss
                        take_profit = adL
                        reward_to_risk = self.calculate_rr(
                            sell_price, stop_loss, take_profit, trade_type="SELL")
                        new_data = pd.DataFrame([["OPENING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "SELL", "XAUUSD", reward_to_risk, None, None, pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
                    elif buy_price and candle_data.Low <= buy_price:
                        # Oleksandr updated 08/02  !!!
                        if buy_was_closed:
                            continue

                        active_order = "BUY"
                        stop_loss = pdLSL
                        stop_loss_on_trade_opening = stop_loss
                        take_profit = adH
                        reward_to_risk = self.calculate_rr(
                            buy_price, stop_loss, take_profit, trade_type="BUY")
                        new_data = pd.DataFrame([["OPENING", hero_date.date(), self.WEEKDAYS[hero_date.weekday()], candle_time, "BUY", "XAUUSD", reward_to_risk, None, None, pdLSH,
                                                pdLSL, adH, adL, sell_price, buy_price, stop_loss, take_profit, candle_data.High, candle_data.Low, candle_data.Close]], columns=report_columns)
                        report_df = pd.concat(
                            [report_df, new_data], ignore_index=True)
            hero_date += timedelta(days=1)
        summary = self.generate_summary(report_df)
        return report_df, summary
