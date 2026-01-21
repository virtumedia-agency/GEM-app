import yfinance as yf
import pandas as pd
from typing import Dict, List

class DataProvider:
    def __init__(self):
        pass

    def get_closes(self, tickers: Dict[str, str], start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """
        Fetches adjusted close prices for the given list of tickers between start_date and end_date.
        
        Args:
            tickers: Dictionary of ticker symbols (e.g. {'US': 'SPY', ...})
            start_date: Start date for data fetch.
            end_date: End date for data fetch.
            
        Returns:
            pd.DataFrame: DataFrame containing Adjusted Close prices. 
                          Columns are the keys from the tickers dict (e.g. 'US', 'EXUS').
        """
        symbols = list(tickers.values())
        
        print(f"Fetching data for {symbols} from {start_date.date()} to {end_date.date()}...")
        
        # Download data
        # auto_adjust=True ensures we get data adjusted for splits and dividends
        # threads=False to be safer in some CI environments, though usually fine
        df = yf.download(symbols, start=start_date, end=end_date + pd.Timedelta(days=1), auto_adjust=True, progress=False, threads=False)
        
        if df.empty:
            raise ValueError("No data fetched from Yahoo Finance.")

        closes = pd.DataFrame()

        # Handle yfinance structure variations
        # Sometimes 'Close' is at top level, sometimes it's under 'Adj Close' (if auto_adjust=False),
        # but with auto_adjust=True, it is usually just 'Close'.
        
        # With auto_adjust=True, columns are typically Open, High, Low, Close, Volume.
        # If multiple tickers, columns are MultiIndex: (Price, Ticker).
        
        target_col = 'Close'
        
        if len(symbols) == 1:
            symbol = symbols[0]
            # If 1 ticker, check if MultiIndex or not
            if isinstance(df.columns, pd.MultiIndex):
                # Access (Close, Ticker)
                try:
                    closes[symbol] = df[target_col][symbol]
                except KeyError:
                    # Maybe level is swapped or just 'Close'
                     closes[symbol] = df[target_col]
            else:
                closes[symbol] = df[target_col]
        else:
            # Multiple tickers
            if target_col in df.columns.levels[0] if isinstance(df.columns, pd.MultiIndex) else target_col in df.columns:
                # Standard MultiIndex case
                if isinstance(df.columns, pd.MultiIndex):
                    closes = df[target_col].copy()
                else:
                    # Should not happen with multiple tickers usually, unless yfinance changes
                    # Fallback
                    closes = df[target_col].copy()
            else:
                # Verify available columns
                available = list(df.columns)
                raise ValueError(f"Could not find '{target_col}' in response. Columns: {available}")

        # Rename columns from Symbols to Keys (SPY -> US)
        # Invert the dictionary to map Symbol -> Key
        symbol_to_key = {v: k for k, v in tickers.items()}
        
        # Filter only columns we requested (in case yfinance returns more or we need to be strict)
        # Also renames them
        closes = closes.rename(columns=symbol_to_key)
        
        # Sort by date just in case
        closes = closes.sort_index()
        
        return closes

    def get_price_at_date(self, prices: pd.DataFrame, target_date: pd.Timestamp) -> pd.Series:
        """
        Gets the price at the specific date. If date is missing (e.g. weekend/holiday), 
        looks back to the nearest previous valid trading day.
        """
        # Filter for dates up to target_date
        # We assume prices are sorted by date
        valid_data = prices.loc[:target_date]
        
        if valid_data.empty:
            raise ValueError(f"No data available before or on {target_date}")
            
        # Return the last row (nearest valid date)
        return valid_data.iloc[-1]
