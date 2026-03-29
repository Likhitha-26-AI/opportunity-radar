"""
ARTHA AI — Portfolio Analyzer
Multi-stock portfolio risk, diversification, and suggestion engine.
"""

import pandas as pd
import numpy as np
from modules.indicators import compute_all_indicators
from modules.signals import generate_signal


# ─── Sector Classification ────────────────────────────────────────────────────

SECTOR_MAP = {
    "RELIANCE.NS": "Energy/Retail",
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "WIPRO.NS": "IT",
    "HCLTECH.NS": "IT",
    "BAJFINANCE.NS": "NBFC",
    "SBIN.NS": "Banking",
    "AXISBANK.NS": "Banking",
    "KOTAKBANK.NS": "Banking",
    "TATAMOTORS.NS": "Auto",
    "MARUTI.NS": "Auto",
    "HEROMOTOCO.NS": "Auto",
    "TATASTEEL.NS": "Metals",
    "HINDALCO.NS": "Metals",
    "JSWSTEEL.NS": "Metals",
    "SUNPHARMA.NS": "Pharma",
    "CIPLA.NS": "Pharma",
    "DRREDDY.NS": "Pharma",
    "DIVISLAB.NS": "Pharma",
    "BHARTIARTL.NS": "Telecom",
    "TITAN.NS": "Consumer",
    "ASIANPAINT.NS": "Consumer",
    "NESTLEIND.NS": "Consumer",
    "BRITANNIA.NS": "Consumer",
    "NTPC.NS": "Power",
    "POWERGRID.NS": "Power",
    "COALINDIA.NS": "Energy",
    "ONGC.NS": "Energy",
    "IOC.NS": "Energy",
    "BPCL.NS": "Energy",
    "LT.NS": "Infrastructure",
    "ULTRACEMCO.NS": "Cement",
    "SHREECEM.NS": "Cement",
    "GRASIM.NS": "Diversified",
    "M&M.NS": "Auto",
    "BAJAJFINSV.NS": "NBFC",
    "INDUSINDBK.NS": "Banking",
    "ADANIPORTS.NS": "Infrastructure",
    "APOLLOHOSP.NS": "Healthcare",
    "DMART.NS": "Retail",
    "TECHM.NS": "IT",
    "EICHERMOT.NS": "Auto",
    "UPL.NS": "Agrochemicals",
    "SBILIFE.NS": "Insurance",
    "HDFCLIFE.NS": "Insurance",
}

BETA_MAP = {
    "Banking": 1.3,
    "NBFC": 1.4,
    "IT": 0.9,
    "Auto": 1.2,
    "Metals": 1.5,
    "Energy": 1.1,
    "Pharma": 0.8,
    "Telecom": 0.9,
    "Consumer": 0.7,
    "Power": 0.8,
    "Infrastructure": 1.1,
    "Cement": 1.0,
    "Diversified": 1.0,
    "Healthcare": 0.8,
    "Retail": 1.0,
    "Insurance": 0.9,
    "Agrochemicals": 1.0,
}


def get_sector(symbol: str) -> str:
    return SECTOR_MAP.get(symbol, "Other")


def get_beta(sector: str) -> float:
    return BETA_MAP.get(sector, 1.0)


# ─── Individual Stock Metrics ─────────────────────────────────────────────────

def analyze_single_stock(symbol: str, df: pd.DataFrame) -> dict:
    """Compute per-stock portfolio metrics."""
    inds = compute_all_indicators(df)
    sig = generate_signal(inds)
    sector = get_sector(symbol)
    beta = get_beta(sector)

    close = df["Close"]
    returns = close.pct_change().dropna()
    volatility = float(returns.std() * np.sqrt(252) * 100)  # annualized %
    drawdown = float(((close - close.cummax()) / close.cummax()).min() * 100)

    return {
        "symbol": symbol.replace(".NS", ""),
        "sector": sector,
        "beta": beta,
        "volatility": round(volatility, 2),
        "max_drawdown": round(drawdown, 2),
        "rsi": inds.get("rsi", 50),
        "trend": inds.get("trend", "SIDEWAYS"),
        "signal": sig.get("signal", "HOLD"),
        "confidence": sig.get("confidence", 50),
        "close": inds.get("close", 0),
    }


# ─── Portfolio Scoring ────────────────────────────────────────────────────────

def compute_risk_score(stock_metrics: list) -> dict:
    """Aggregate portfolio risk score 0-100 (lower = safer)."""
    if not stock_metrics:
        return {"score": 0, "label": "N/A", "breakdown": {}}

    avg_beta = np.mean([s["beta"] for s in stock_metrics])
    avg_volatility = np.mean([s["volatility"] for s in stock_metrics])
    avg_drawdown = abs(np.mean([s["max_drawdown"] for s in stock_metrics]))
    avoid_count = sum(1 for s in stock_metrics if s["signal"] in ("AVOID", "CAUTION"))

    beta_score = min(40, (avg_beta - 0.5) / 1.5 * 40)
    vol_score = min(30, avg_volatility / 60 * 30)
    dd_score = min(20, avg_drawdown / 40 * 20)
    signal_penalty = avoid_count / len(stock_metrics) * 10

    total = beta_score + vol_score + dd_score + signal_penalty

    if total < 25:
        label = "LOW RISK"
    elif total < 45:
        label = "MODERATE RISK"
    elif total < 65:
        label = "HIGH RISK"
    else:
        label = "VERY HIGH RISK"

    return {
        "score": round(total, 1),
        "label": label,
        "breakdown": {
            "Beta Contribution": round(beta_score, 1),
            "Volatility Contribution": round(vol_score, 1),
            "Drawdown Contribution": round(dd_score, 1),
            "Signal Penalty": round(signal_penalty, 1),
        },
        "avg_beta": round(avg_beta, 2),
        "avg_volatility": round(avg_volatility, 1),
        "avg_drawdown": round(avg_drawdown, 1),
    }


def compute_diversification_score(stock_metrics: list) -> dict:
    """Score diversification 0-100 (higher = more diversified)."""
    if not stock_metrics:
        return {"score": 0, "label": "N/A", "sectors": {}}

    sectors = [s["sector"] for s in stock_metrics]
    sector_counts = pd.Series(sectors).value_counts().to_dict()
    n_stocks = len(stock_metrics)
    n_sectors = len(sector_counts)
    max_concentration = max(sector_counts.values()) / n_stocks

    sector_score = min(50, n_sectors / 8 * 50)
    concentration_score = (1 - max_concentration) * 50
    total = sector_score + concentration_score

    if total >= 75:
        label = "WELL DIVERSIFIED"
    elif total >= 50:
        label = "MODERATE DIVERSIFICATION"
    elif total >= 30:
        label = "CONCENTRATED"
    else:
        label = "HIGHLY CONCENTRATED"

    return {
        "score": round(total, 1),
        "label": label,
        "sectors": sector_counts,
        "n_sectors": n_sectors,
        "dominant_sector": max(sector_counts, key=sector_counts.get),
    }


# ─── Portfolio Suggestions ────────────────────────────────────────────────────

def generate_suggestions(stock_metrics: list, risk: dict, diversification: dict) -> list:
    """Generate actionable portfolio improvement suggestions."""
    suggestions = []
    sectors = diversification.get("sectors", {})
    n_sectors = diversification.get("n_sectors", 0)
    dominant = diversification.get("dominant_sector", "")
    risk_score = risk.get("score", 50)
    avg_beta = risk.get("avg_beta", 1.0)

    # Concentration risk
    if sectors and max(sectors.values()) / sum(sectors.values()) > 0.4:
        suggestions.append({
            "type": "DIVERSIFICATION",
            "priority": "HIGH",
            "text": f"⚠️ Over-concentrated in **{dominant}** ({sectors[dominant]} stocks). Reduce to max 30% per sector.",
        })

    # Too few sectors
    if n_sectors < 3:
        missing = ["Pharma", "Consumer", "Infrastructure", "IT"]
        missing_filtered = [s for s in missing if s not in sectors][:2]
        suggestions.append({
            "type": "DIVERSIFICATION",
            "priority": "MEDIUM",
            "text": f"📌 Only {n_sectors} sector(s) covered. Consider adding: **{', '.join(missing_filtered)}** for better diversification.",
        })

    # High beta portfolio
    if avg_beta > 1.3:
        suggestions.append({
            "type": "RISK_REDUCTION",
            "priority": "HIGH",
            "text": f"🔴 Portfolio Beta: **{avg_beta:.2f}** — highly market-sensitive. Add defensive stocks (Pharma, FMCG, Power) to reduce beta.",
        })

    # Avoid/Caution signals
    avoid_stocks = [s["symbol"] for s in stock_metrics if s["signal"] in ("AVOID", "CAUTION")]
    if avoid_stocks:
        suggestions.append({
            "type": "SIGNAL_ALERT",
            "priority": "HIGH",
            "text": f"🚨 Weak technicals detected in: **{', '.join(avoid_stocks)}**. Consider reducing exposure or setting stop-losses.",
        })

    # Strong opportunities
    strong_buy = [s["symbol"] for s in stock_metrics if s["signal"] in ("STRONG_BUY", "BUY")]
    if strong_buy:
        suggestions.append({
            "type": "OPPORTUNITY",
            "priority": "LOW",
            "text": f"🚀 Technically strong picks: **{', '.join(strong_buy)}**. Consider adding on dips.",
        })

    # Good shape
    if risk_score < 30 and n_sectors >= 4:
        suggestions.append({
            "type": "POSITIVE",
            "priority": "INFO",
            "text": "✅ Portfolio structure is healthy. Maintain discipline with stop-losses and periodic rebalancing.",
        })

    return suggestions


# ─── Master Portfolio Analyzer ────────────────────────────────────────────────

def analyze_portfolio(stock_data_dict: dict) -> dict:
    """
    Input: {symbol: df}
    Output: Full portfolio analysis report
    """
    stock_metrics = []
    for symbol, df in stock_data_dict.items():
        if not df.empty and len(df) >= 20:
            metrics = analyze_single_stock(symbol, df)
            stock_metrics.append(metrics)

    if not stock_metrics:
        return {"error": "No valid data found for portfolio stocks."}

    risk = compute_risk_score(stock_metrics)
    diversification = compute_diversification_score(stock_metrics)
    suggestions = generate_suggestions(stock_metrics, risk, diversification)

    return {
        "stock_metrics": stock_metrics,
        "risk": risk,
        "diversification": diversification,
        "suggestions": suggestions,
        "stock_count": len(stock_metrics),
    }
