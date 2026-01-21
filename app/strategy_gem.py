import pandas as pd
from typing import Dict, Any

class GemStrategy:
    def __init__(self, config: Dict):
        self.tickers_map = config['tickers'] # US -> SPY, etc.
        self.lookback_months = config['strategy']['lookback_months']

    def calculate_decision(self, prices_t: pd.Series, prices_t_minus_12: pd.Series) -> Dict[str, Any]:
        """
        Calculates GEM decision based on two price points.
        
        Args:
            prices_t: Prices at current point (month end).
            prices_t_minus_12: Prices 12 months ago.
            
        Returns:
            Dict containing decision, momentum values, and context.
        """
        
        # 1. Calculate Returns
        # Return = (Price_t / Price_t-12) - 1
        returns = (prices_t / prices_t_minus_12) - 1
        
        us_ret = returns['US']
        exus_ret = returns['EXUS']
        cash_proxy_ret = returns['CASH_PROXY']
        
        # Ensure we handle potential missing values if needed, 
        # but DataProvider should have handled obtaining valid prices.
        
        # 2. Logic
        mode = "RISK-OFF"
        selected_asset = "BONDS" # Default
        
        # Condition 1: US vs Cash
        # PRD 4.3: If US > CASH_PROXY -> RISK-ON
        if us_ret > cash_proxy_ret:
            mode = "RISK-ON"
            # Condition 2: Select max momentum (US vs EXUS)
            if us_ret >= exus_ret:
                selected_asset = "US"
            else:
                selected_asset = "EXUS"
        else:
            # PRD 4.2: If US <= CASH_PROXY -> RISK-OFF -> BONDS
            mode = "RISK-OFF"
            selected_asset = "BONDS"
            
        # Get the actual ticker for the selected asset
        selected_ticker = self.tickers_map[selected_asset]

        return {
            "mode": mode,
            "selected_asset_key": selected_asset,
            "selected_ticker": selected_ticker,
            "momentum": {
                "US": us_ret,
                "EXUS": exus_ret,
                "CASH_PROXY": cash_proxy_ret,
                "BONDS": returns.get('BONDS', 0.0)
            },
            "prices_current": prices_t.to_dict(),
            "prices_prev": prices_t_minus_12.to_dict()
        }
