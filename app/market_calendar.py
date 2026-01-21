import pandas as pd
from datetime import date, timedelta

class MarketCalendar:
    @staticmethod
    def get_last_trading_session_last_month(current_date: date) -> pd.Timestamp:
        """
        Calculates the last business day of the previous calendar month.
        
        Args:
            current_date (date): The current date (usually the execution date).
            
        Returns:
            pd.Timestamp: The timestamp of the last business day of the previous month.
        """
        # First day of current month
        first_of_current = current_date.replace(day=1)
        # Last day of previous month
        last_of_prev = first_of_current - timedelta(days=1)
        
        # Use pandas BMonthEnd to find the nearest previous business day end of month
        # rollback will move to the month end on or before the date
        return pd.tseries.offsets.BMonthEnd().rollback(last_of_prev)

    @staticmethod
    def get_lookback_date(reference_date: pd.Timestamp, months: int) -> pd.Timestamp:
        """
        Calculates the date 'months' ago.
        
        Args:
            reference_date (pd.Timestamp): The end date.
            months (int): Number of months to look back.
            
        Returns:
            pd.Timestamp: The date months ago.
        """
        return reference_date - pd.DateOffset(months=months)
