import os
import sys
import yaml
import pandas as pd
import logging
from datetime import date
from dotenv import load_dotenv

# Import modules
from market_calendar import MarketCalendar
from data_provider import DataProvider
from strategy_gem import GemStrategy
from reporter import Reporter
from email_resend import EmailSender

# Setup Logging
LOG_DIR = "app/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
    
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)
logger = logging.getLogger(__name__)

def load_config(path="app/config/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def append_history(decision, date_point, filename="decisions.csv"):
    file_exists = os.path.isfile(filename)
    
    # Flatten dict for csv
    record = {
        "date": date_point.date(),
        "selected_asset": decision['selected_asset_key'],
        "ticker": decision['selected_ticker'],
        "mode": decision['mode'],
        "momentum_us": decision['momentum']['US'],
        "momentum_exus": decision['momentum']['EXUS'],
        "momentum_cash": decision['momentum']['CASH_PROXY'],
        "timestamp": pd.Timestamp.now()
    }
    
    df = pd.DataFrame([record])
    
    if not file_exists:
        df.to_csv(filename, index=False)
    else:
        df.to_csv(filename, mode='a', header=False, index=False)

def main():
    logger.info("Starting GEM ETF Decision App")
    load_dotenv() # Load .env if present
    
    try:
        # 1. Configuration
        config = load_config()
        
        # Override email config with environment variables if present (Security best practice)
        if os.getenv("EMAIL_FROM"):
            config['email']['from'] = os.getenv("EMAIL_FROM")
        if os.getenv("EMAIL_TO"):
            config['email']['to'] = os.getenv("EMAIL_TO")
            
        logger.info("Configuration loaded.")
        
        # 2. Determine Dates
        today = date.today()
        # Ensure we are looking at the end of the previous month
        analysis_date = MarketCalendar.get_last_trading_session_last_month(today)
        logger.info(f"Analysis Date (End of Last Month): {analysis_date.date()}")
        
        likback_months = config['strategy']['lookback_months']
        # We need data from 12 months prior to analysis_date
        # To be safe with fetch, we go back a bit further
        comparison_date_approx = MarketCalendar.get_lookback_date(analysis_date, likback_months)
        fetch_start_date = comparison_date_approx - pd.DateOffset(months=1) # Buffer
        
        logger.info(f"Fetching data from approx {fetch_start_date.date()} to {analysis_date.date()}")
        
        # 3. Data Provider
        dp = DataProvider()
        prices_df = dp.get_closes(config['tickers'], fetch_start_date, analysis_date)
        
        # Extract specific price points
        current_prices = dp.get_price_at_date(prices_df, analysis_date)
        
        # Get price exactly lookback_months ago (or closest previous trading day)
        # We look for the price at (analysis_date - 12 months)
        # Re-calculate exact target date for strategy
        target_prev_date = analysis_date - pd.DateOffset(months=likback_months)
        
        # We need to find the closes valid trading day on or before target_prev_date
        prev_prices = dp.get_price_at_date(prices_df, target_prev_date)
        
        logger.info(f"Price Current ({current_prices.name.date() if hasattr(current_prices.name, 'date') else current_prices.name}):\n{current_prices.to_dict()}")
        logger.info(f"Price Previous ({prev_prices.name.date() if hasattr(prev_prices.name, 'date') else prev_prices.name}):\n{prev_prices.to_dict()}")
        
        # 4. Strategy
        strat = GemStrategy(config)
        decision = strat.calculate_decision(current_prices, prev_prices)
        logger.info(f"Decision Calculated: {decision['selected_asset_key']} ({decision['mode']})")
        
        # 5. Reporting
        reporter = Reporter()
        report_content = reporter.generate_report_content(decision, analysis_date, config['tickers'])
        report_path = reporter.save_report(report_content, analysis_date.strftime('%Y-%m'))
        logger.info(f"Report saved to {report_path}")
        
        # 6. Email
        subject = f"{config['email']['subject_prefix']} - {analysis_date.strftime('%Y-%m')} ({decision['mode']})"
        email_sender = EmailSender(config)
        email_sender.send_email(subject, report_content)
        
        # 7. History
        append_history(decision, analysis_date, filename="app/decisions.csv")
        logger.info("History updated.")
        
        logger.info("Execution completed successfully.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
