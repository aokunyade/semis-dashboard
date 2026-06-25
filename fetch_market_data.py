"""Fetch market data for every ticker in config/sectors.json via yfinance.

Output: data/market.json  ->  {"updated": ISO8601, "stocks": {ticker: {...}}}
Per-ticker fields: last, cur (currency), ret1d, ret1w, ret1m, retYtd, ret1y, ret5y,
                   mktCap, val, valLabel.

Run from repo root:  python scripts/fetch_market_data.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent


def load_tickers():
    cfg = json.loads((ROOT / "sectors.json").read_text())
    seen, out = set(), []
    for sec in cfg["sectors"]:
        for row in sec["tickers"]:
            if row["t"] not in seen:
                seen.add(row["t"])
                out.append(row["t"])
    return out


def pct(last, past):
    try:
        return round(100 * (last / past - 1), 1)
    except Exception:
        return None


def fetch(tickers):
    out = {}
    hist = yf.download(tickers, period="5y", interval="1d", auto_adjust=True,
                       progress=False, group_by="ticker", threads=True)
    multi = isinstance(hist.columns, pd.MultiIndex)
    for t in tickers:
        try:
            px = (hist[t]["Close"].dropna() if multi else hist["Close"].dropna())
            if px.empty:
                print(f"  {t}: no price history")
                continue
            last = float(px.iloc[-1])
            idx = px.index

            def ret_days(days):
                target = idx[-1] - pd.Timedelta(days=days)
                older = px[idx <= target]
                return pct(last, float(older.iloc[-1])) if len(older) else None

            rec = {
                "last": round(last, 2),
                "ret1d": pct(last, float(px.iloc[-2])) if len(px) > 1 else None,
                "ret1w": ret_days(7),
                "ret1m": ret_days(30),
                "ret1y": ret_days(365),
                "ret5y": ret_days(365 * 5),
            }
            ytd = px[idx >= datetime(idx[-1].year, 1, 1).strftime("%Y-%m-%d")]
            rec["retYtd"] = pct(last, float(ytd.iloc[0])) if len(ytd) > 1 else None

            # valuation + market cap + currency from .info (best-effort)
            try:
                info = yf.Ticker(t).info or {}
            except Exception:
                info = {}
            rec["cur"] = info.get("currency") or "USD"
            rec["mktCap"] = info.get("marketCap")
            pe = info.get("trailingPE")
            ps = info.get("priceToSalesTrailing12Months")
            if pe and pe > 0:
                rec["val"], rec["valLabel"] = round(pe, 1), "P/E"
            elif ps and ps > 0:
                rec["val"], rec["valLabel"] = round(ps, 1), "P/S"
            out[t] = rec
        except Exception as e:
            print(f"  {t}: failed ({e})")
    return out


def main():
    tickers = load_tickers()
    print(f"fetching {len(tickers)} tickers ...")
    stocks = fetch(tickers)
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stocks": stocks,
    }
    
    (ROOT / "market.json").write_text(json.dumps(payload))
    print(f"wrote data/market.json ({len(stocks)}/{len(tickers)} tickers)")


if __name__ == "__main__":
    main()
