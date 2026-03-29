"""
ARTHA AI — Data Fetch Engine
Handles all NSE stock data retrieval via yfinance.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import time

# ─── Symbol Normalization ────────────────────────────────────────────────────

KNOWN_SYMBOLS = {
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "hdfc": "HDFCBANK.NS",
    "hdfcbank": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "icicibank": "ICICIBANK.NS",
    "wipro": "WIPRO.NS",
    "ltim": "LTIM.NS",
    "hcl": "HCLTECH.NS",
    "hcltech": "HCLTECH.NS",
    "bajaj": "BAJFINANCE.NS",
    "bajajfinance": "BAJFINANCE.NS",
    "sbi": "SBIN.NS",
    "axisbank": "AXISBANK.NS",
    "axis": "AXISBANK.NS",
    "kotak": "KOTAKBANK.NS",
    "kotakbank": "KOTAKBANK.NS",
    "maruti": "MARUTI.NS",
    "tatamotors": "TATAMOTORS.NS",
    "tata": "TATAMOTORS.NS",
    "tatasteel": "TATASTEEL.NS",
    "sunpharma": "SUNPHARMA.NS",
    "sun": "SUNPHARMA.NS",
    "adani": "ADANIPORTS.NS",
    "adaniports": "ADANIPORTS.NS",
    "asianpaint": "ASIANPAINT.NS",
    "asian": "ASIANPAINT.NS",
    "ultracemco": "ULTRACEMCO.NS",
    "bharti": "BHARTIARTL.NS",
    "airtel": "BHARTIARTL.NS",
    "bhartiartl": "BHARTIARTL.NS",
    "nestleindia": "NESTLEIND.NS",
    "nestle": "NESTLEIND.NS",
    "titan": "TITAN.NS",
    "powergrid": "POWERGRID.NS",
    "ntpc": "NTPC.NS",
    "ongc": "ONGC.NS",
    "ioc": "IOC.NS",
    "indusindbank": "INDUSINDBK.NS",
    "drreddy": "DRREDDY.NS",
    "dr": "DRREDDY.NS",
    "hindalco": "HINDALCO.NS",
    "jswsteel": "JSWSTEEL.NS",
    "jsw": "JSWSTEEL.NS",
    "m&m": "M&M.NS",
    "mm": "M&M.NS",
    "mahindra": "M&M.NS",
    "cipla": "CIPLA.NS",
    "divislab": "DIVISLAB.NS",
    "divis": "DIVISLAB.NS",
    "britannia": "BRITANNIA.NS",
    "grasim": "GRASIM.NS",
    "sbilife": "SBILIFE.NS",
    "hdfclife": "HDFCLIFE.NS",
    "techm": "TECHM.NS",
    "techmahindra": "TECHM.NS",
    "bajajfinsv": "BAJAJFINSV.NS",
    "eichermotors": "EICHERMOT.NS",
    "eicher": "EICHERMOT.NS",
    "upl": "UPL.NS",
    "shreecem": "SHREECEM.NS",
    "lt": "LT.NS",
    "ltinfotech": "LTI.NS",
    "apollohosp": "APOLLOHOSP.NS",
    "apollo": "APOLLOHOSP.NS",
    "heromotoco": "HEROMOTOCO.NS",
    "hero": "HEROMOTOCO.NS",
    "coal": "COALINDIA.NS",
    "coalindia": "COALINDIA.NS",
    "bpcl": "BPCL.NS",
    "siemens": "SIEMENS.NS",
    "dmart": "DMART.NS",
    "avenue": "DMART.NS",
}

# Default radar stocks for Opportunity Scanner
RADAR_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "WIPRO.NS", "BAJFINANCE.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "SUNPHARMA.NS", "BHARTIARTL.NS",
    "TITAN.NS", "NTPC.NS", "ONGC.NS", "HCLTECH.NS", "M&M.NS", "LT.NS",
]


def normalize_symbol(raw: str) -> str:
    """Convert user input to valid NSE ticker symbol."""
    clean = raw.strip().lower().replace(" ", "")
    if clean in KNOWN_SYMBOLS:
        return KNOWN_SYMBOLS[clean]
    upper = raw.strip().upper()
    if upper.endswith(".NS") or upper.endswith(".BO"):
        return upper
    return upper + ".NS"


@st.cache_data(ttl=60)
def fetch_stock_data(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data for a given NSE symbol.
    Returns empty DataFrame on failure.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_stock_info(symbol: str) -> dict:
    """Fetch metadata/info for a stock."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "current_price": info.get("currentPrice", None),
            "currency": info.get("currency", "INR"),
        }
    except Exception:
        return {"name": symbol, "sector": "N/A", "industry": "N/A"}


@st.cache_data(ttl=60)
def fetch_multiple_stocks(symbols: list, period: str = "3mo") -> dict:
    """Fetch data for multiple stocks. Returns dict of {symbol: df}."""
    results = {}
    for sym in symbols:
        df = fetch_stock_data(sym, period=period)
        if not df.empty:
            results[sym] = df
        time.sleep(0.05)  # gentle rate limiting
    return results


def get_current_price(symbol: str) -> float:
    """Get the most recent closing price."""
    df = fetch_stock_data(symbol, period="5d")
    if df.empty:
        return 0.0
    return float(df["Close"].iloc[-1])


def validate_symbol(symbol: str) -> bool:
    """Check if symbol returns valid data."""
    df = fetch_stock_data(symbol, period="5d")
    return not df.empty
