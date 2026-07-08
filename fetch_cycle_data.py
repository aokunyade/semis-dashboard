"""Compute semiconductor cycle indicators -> cycle.json

Indicators:
  1. soxSpx    - SOX/SPX ratio vs 1y average (momentum)
  2. soxPe     - cap-weighted trailing P/E of SOX bellwethers vs 10y baseline (valuation)
  3. invDays   - aggregate inventory days across USD-reporting bellwethers vs year-ago
  4. analogYoY - TXN+ADI+MCHP+NXPI revenue YoY (classic early-cycle tell)
  5. memRel3m  - memory basket vs SOX, 3-month relative return (cycle temperature)
  6. capexYoY  - AMZN+MSFT+GOOGL+META+ORCL quarterly capex YoY (demand engine)
  7. fredIp    - US semiconductor industrial production YoY (FRED IPG3344S)
  8. sentiment - WSJ headline tone last 30d via Google News RSS (bubble vs demand talk)

Composite: each signal scored -1 (cold/trough) .. +1 (hot/late-cycle), averaged,
mapped to a phase label. Fully transparent -- see score() at bottom.

Run from repo root: python fetch_cycle_data.py   ->  writes cycle.json
"""
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parent

# ---- config ----------------------------------------------------------------
# 10y average trailing P/E baseline for the SOX. No free historical series
# exists, so this is a static, editable anchor (institutional cites cluster
# ~19-21x forward / ~25x trailing over 2016-2025). Update annually.
SOX_PE_10Y_AVG = 25.0

SOX_PE_NAMES = ["NVDA", "AVGO", "AMD", "TSM", "QCOM", "TXN", "ADI", "INTC", "MU",
                "AMAT", "LRCX", "KLAC", "MRVL", "NXPI", "MCHP", "ON", "MPWR", "TER"]

# USD reporters only (mixing currencies would corrupt the aggregate)
INV_NAMES = ["NVDA", "AMD", "AVGO", "QCOM", "MRVL", "TXN", "ADI", "MCHP", "NXPI",
             "ON", "INTC", "MU", "AMAT", "LRCX", "KLAC", "TER", "GFS", "MPWR"]

ANALOG_NAMES = ["TXN", "ADI", "MCHP", "NXPI"]
MEMORY_NAMES = ["MU", "000660.KS", "285A.T"]  # Micron, SK Hynix, Kioxia (local ccy, relative return only)
CAPEX_NAMES = ["AMZN", "MSFT", "GOOGL", "META", "ORCL"]

RSS_URL = ("https://news.google.com/rss/search?"
           "q=semiconductor+OR+chips+OR+chipmaker+site:wsj.com+when:30d"
           "&hl=en-US&gl=US&ceid=US:en")

BUBBLE_WORDS = ["bubble", "overbuild", "overcapacity", "oversupply", "glut", "froth",
                "overheated", "correction", "crash", "selloff", "sell-off", "slump",
                "downturn", "cancel", "pullback", "slowdown", "cooling", "burst",
                "warn", "doubts", "skeptic", "fears", "stretched", "circular",
                "too far", "cracks", "reckoning", "unravel",
                # bearish market action / risk-off language (was missing -- bearish
                # headlines were falling through to neutral or even "demand")
                "tumble", "plunge", "sink", "slide", "slid", "stumble", "retreat",
                "rout", "swoon", "dive", "drop", "falls", "fell", "losses",
                "bear territory", "bear market", "short bet", "short seller",
                "short-sell", "worries", "worry", "concern", "jitters", "danger",
                "weak", "misses", "cuts", "turmoil", "question", "fizzle",
                "pull back", "pulls back", "beginning of the end"]
DEMAND_WORDS = ["demand", "shortage", "record", "surge", "boom", "capex", "expansion",
                "ramp", "sold out", "tight", "orders", "beats", "raises", "accelerat",
                "upgrade", "rally", "growth", "buildout",
                "insatiable", "supercycle", "breakneck", "all-time high"]

# Only score headlines actually about semis/AI-compute -- the Google News query
# matches "chips" loosely and pulls in oil, banks, shipbuilders etc., which
# polluted the tone counts.
RELEVANT_RE = re.compile(
    r"\b(chips?|chipmakers?|chip-?stacking|semiconductors?|semis|nvidia|tsmc|amd"
    r"|intel|micron|hynix|samsung|foundry|wafers?|memory|dram|nand|hbm|gpus?"
    r"|asics?|ai|data.?centers?|hyperscalers?|lithography|asml|broadcom|qualcomm"
    r"|sox)\b")


def pct(a, b):
    try:
        return round(100 * (a / b - 1), 1)
    except Exception:
        return None


def monthly_series(px, years=10):
    m = px.resample("ME").last().dropna().tail(years * 12)
    return [[d.strftime("%Y-%m"), round(float(v), 3)] for d, v in m.items()]


# ---- 1. SOX/SPX ratio -------------------------------------------------------
def sox_spx():
    h = yf.download(["^SOX", "^GSPC"], period="10y", interval="1d",
                    auto_adjust=True, progress=False, group_by="ticker")
    ratio = (h["^SOX"]["Close"] / h["^GSPC"]["Close"]).dropna()
    last = float(ratio.iloc[-1])
    avg1y = float(ratio.tail(252).mean())
    return {"value": round(last, 3), "vsAvg1y": pct(last, avg1y),
            "series": monthly_series(ratio)}


# ---- 2. SOX multiple vs 10y baseline ---------------------------------------
def sox_pe():
    cap_sum, earn_sum, used = 0.0, 0.0, 0
    for t in SOX_PE_NAMES:
        try:
            info = yf.Ticker(t).info or {}
            cap, pe = info.get("marketCap"), info.get("trailingPE")
            if cap and pe and pe > 0:
                cap_sum += cap
                earn_sum += cap / pe   # implied trailing earnings
                used += 1
        except Exception:
            pass
    if not earn_sum:
        return None
    pe_now = cap_sum / earn_sum        # cap-weighted harmonic mean
    return {"value": round(pe_now, 1), "avg10y": SOX_PE_10Y_AVG,
            "premium": pct(pe_now, SOX_PE_10Y_AVG), "names": used}


# ---- 3. aggregate inventory days -------------------------------------------
def inventory_days():
    inv_by_q, cogs_by_q = {}, {}
    for t in INV_NAMES:
        try:
            tk = yf.Ticker(t)
            bs, inc = tk.quarterly_balance_sheet, tk.quarterly_income_stmt
            if bs is None or inc is None or bs.empty or inc.empty:
                continue
            inv_row = bs.loc["Inventory"] if "Inventory" in bs.index else None
            cogs_row = inc.loc["Cost Of Revenue"] if "Cost Of Revenue" in inc.index else None
            if inv_row is None or cogs_row is None:
                continue
            for q in bs.columns:
                if q in inc.columns and pd.notna(inv_row[q]) and pd.notna(cogs_row[q]) and cogs_row[q]:
                    key = q.strftime("%Y-%m")
                    inv_by_q.setdefault(key, {})[t] = float(inv_row[q])
                    cogs_by_q.setdefault(key, {})[t] = float(cogs_row[q])
        except Exception as e:
            print(f"  inv {t}: {e}")
    # only quarters where we have a consistent, broad sample
    series = []
    for q in sorted(inv_by_q):
        names = set(inv_by_q[q]) & set(cogs_by_q.get(q, {}))
        if len(names) >= 8:
            days = sum(inv_by_q[q][n] for n in names) / sum(cogs_by_q[q][n] for n in names) * 91
            series.append([q, round(days, 1), len(names)])
    if not series:
        return None
    latest = series[-1]
    yr_ago = next((s for s in reversed(series[:-1])
                   if 320 <= (pd.Timestamp(latest[0]) - pd.Timestamp(s[0])).days <= 420), None)
    return {"value": latest[1], "names": latest[2],
            "yearAgo": yr_ago[1] if yr_ago else None,
            "delta": round(latest[1] - yr_ago[1], 1) if yr_ago else None,
            "series": [[q, d] for q, d, _ in series]}


# ---- 4. analog revenue YoY --------------------------------------------------
def analog_yoy():
    rev_by_q = {}
    for t in ANALOG_NAMES:
        try:
            inc = yf.Ticker(t).quarterly_income_stmt
            if inc is None or inc.empty or "Total Revenue" not in inc.index:
                continue
            for q, v in inc.loc["Total Revenue"].items():
                if pd.notna(v):
                    rev_by_q.setdefault(q.strftime("%Y-%m"), {})[t] = float(v)
        except Exception as e:
            print(f"  analog {t}: {e}")
    qs = sorted(q for q, d in rev_by_q.items() if len(d) == len(ANALOG_NAMES))
    if len(qs) < 5:
        qs = sorted(q for q, d in rev_by_q.items() if len(d) >= 3)
    series, yoy = [], None
    for q in qs:
        names = rev_by_q[q]
        prior = next((p for p in qs if 320 <= (pd.Timestamp(q) - pd.Timestamp(p)).days <= 420
                      and set(rev_by_q[p]) >= set(names)), None)
        if prior:
            cur = sum(names.values())
            old = sum(rev_by_q[prior][n] for n in names)
            series.append([q, pct(cur, old)])
    if series:
        yoy = series[-1][1]
        prev = series[-2][1] if len(series) > 1 else None
        return {"value": yoy, "prev": prev, "series": series}
    return None


# ---- 5. memory vs SOX, 3m relative -----------------------------------------
def memory_rel():
    h = yf.download(MEMORY_NAMES + ["^SOX"], period="1y", interval="1d",
                    auto_adjust=True, progress=False, group_by="ticker")
    rets = []
    for t in MEMORY_NAMES:
        try:
            px = h[t]["Close"].dropna()
            r = pct(float(px.iloc[-1]), float(px[px.index <= px.index[-1] - pd.Timedelta(days=91)].iloc[-1]))
            if r is not None:
                rets.append(r)
        except Exception:
            pass
    sox = h["^SOX"]["Close"].dropna()
    sox3m = pct(float(sox.iloc[-1]), float(sox[sox.index <= sox.index[-1] - pd.Timedelta(days=91)].iloc[-1]))
    if not rets or sox3m is None:
        return None
    basket = sum(rets) / len(rets)
    return {"value": round(basket - sox3m, 1), "basket3m": round(basket, 1), "sox3m": sox3m}


# ---- 6. hyperscaler capex YoY ----------------------------------------------
def capex_yoy():
    cap_by_q = {}
    for t in CAPEX_NAMES:
        try:
            cf = yf.Ticker(t).quarterly_cashflow
            if cf is None or cf.empty or "Capital Expenditure" not in cf.index:
                continue
            for q, v in cf.loc["Capital Expenditure"].items():
                if pd.notna(v):
                    cap_by_q.setdefault(q.strftime("%Y-%m"), {})[t] = abs(float(v))
        except Exception as e:
            print(f"  capex {t}: {e}")
    qs = sorted(q for q, d in cap_by_q.items() if len(d) >= 4)
    series = []
    for q in qs:
        names = cap_by_q[q]
        prior = next((p for p in qs if 320 <= (pd.Timestamp(q) - pd.Timestamp(p)).days <= 420
                      and set(cap_by_q[p]) >= set(names)), None)
        if prior:
            cur = sum(names.values())
            old = sum(cap_by_q[prior][n] for n in names)
            series.append([q, pct(cur, old), round(cur / 1e9, 1)])
    if not series:
        return None
    latest = series[-1]
    return {"value": latest[1], "latestQB": latest[2],
            "series": [[q, y] for q, y, _ in series]}


# ---- 7. FRED semiconductor industrial production ----------------------------
def fred_ip():
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=IPG3344S", timeout=30)
    df = pd.read_csv(StringIO(r.text))
    df.columns = ["date", "v"]
    df["v"] = pd.to_numeric(df["v"], errors="coerce")
    df = df.dropna()
    df["yoy"] = df["v"].pct_change(12) * 100
    df = df.dropna().tail(120)
    series = [[d[:7], round(y, 1)] for d, y in zip(df["date"], df["yoy"])]
    return {"value": series[-1][1], "prev": series[-2][1], "asOf": series[-1][0],
            "series": series}


# ---- 8. WSJ headline sentiment ----------------------------------------------
def sentiment():
    r = requests.get(RSS_URL, timeout=30,
                     headers={"User-Agent": "Mozilla/5.0 (cycle-dashboard)"})
    root = ET.fromstring(r.content)
    items = root.findall(".//item")
    bubble = demand = neutral = 0
    b7 = d7 = 0
    now = datetime.now(timezone.utc)
    tagged = []
    for it in items[:80]:
        title = (it.findtext("title") or "").strip()
        low = title.lower()
        if not RELEVANT_RE.search(low):
            continue  # off-topic (oil, banks, shipping...) -- don't score
        recent = False
        try:
            recent = (now - parsedate_to_datetime(it.findtext("pubDate"))).days < 7
        except Exception:
            pass
        b = sum(1 for w in BUBBLE_WORDS if w in low)
        d = sum(1 for w in DEMAND_WORDS if w in low)
        # tie goes to bubble: warning language ("rally into danger zone",
        # "chips pull back in mixed day") is usually the point of the headline
        if b > d or (b and b == d):
            bubble += 1
            b7 += recent
            tag = "bubble"
        elif d > b:
            demand += 1
            d7 += recent
            tag = "demand"
        else:
            neutral += 1
            tag = "neutral"
        if tag != "neutral" and len(tagged) < 10:
            tagged.append({"t": re.sub(r"\s+-\s+WSJ.*$", "", title), "tag": tag})
    total = bubble + demand
    score = round((bubble - demand) / total, 2) if total else 0.0
    score7 = round((b7 - d7) / (b7 + d7), 2) if (b7 + d7) else None
    return {"score": score, "bubble": bubble, "demand": demand, "neutral": neutral,
            "bubble7": b7, "demand7": d7, "score7": score7,
            "total": bubble + demand + neutral, "headlines": tagged}


# ---- composite ---------------------------------------------------------------
def score(ind):
    """Each signal -> heat in [-1, +1]. +1 = hot/late-cycle, -1 = cold/trough."""
    s = {}
    v = ind.get("soxSpx")
    if v:
        s["soxSpx"] = 1 if v["vsAvg1y"] > 10 else (-1 if v["vsAvg1y"] < -10 else 0)
    v = ind.get("soxPe")
    if v and v.get("premium") is not None:
        s["soxPe"] = 1 if v["premium"] > 20 else (-1 if v["premium"] < -10 else 0)
    v = ind.get("invDays")
    if v and v.get("delta") is not None:
        s["invDays"] = 1 if v["delta"] > 5 else (-1 if v["delta"] < -5 else 0)
    v = ind.get("analogYoY")
    if v and v.get("value") is not None:
        s["analogYoY"] = 1 if v["value"] > 15 else (-1 if v["value"] < 0 else 0)
    v = ind.get("memRel3m")
    if v:
        s["memRel3m"] = 1 if v["value"] > 10 else (-1 if v["value"] < -10 else 0)
    v = ind.get("capexYoY")
    if v and v.get("value") is not None:
        s["capexYoY"] = 1 if v["value"] > 40 else (-1 if v["value"] < 0 else 0)
    v = ind.get("fredIp")
    if v:
        s["fredIp"] = 1 if v["value"] > 15 else (-1 if v["value"] < 0 else 0)
    v = ind.get("sentiment")
    if v and (v["bubble"] + v["demand"]) >= 5:
        s["sentiment"] = 1 if v["score"] > 0.3 else (-1 if v["score"] < -0.3 else 0)
    if not s:
        return None
    avg = sum(s.values()) / len(s)
    if avg < -0.5:
        phase = "Trough"
    elif avg < -0.1:
        phase = "Early expansion"
    elif avg < 0.35:
        phase = "Mid expansion"
    elif avg < 0.65:
        phase = "Late expansion"
    else:
        phase = "Peak / downturn risk"
    return {"score": round(avg, 2), "phase": phase, "signals": s}


def main():
    ind = {}
    for name, fn in [("soxSpx", sox_spx), ("soxPe", sox_pe), ("invDays", inventory_days),
                     ("analogYoY", analog_yoy), ("memRel3m", memory_rel),
                     ("capexYoY", capex_yoy), ("fredIp", fred_ip), ("sentiment", sentiment)]:
        try:
            print(f"computing {name} ...")
            ind[name] = fn()
        except Exception as e:
            print(f"  {name} FAILED: {e}")
            ind[name] = None
    payload = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "indicators": ind, "composite": score(ind)}
    (ROOT / "cycle.json").write_text(json.dumps(payload))
    ok = sum(1 for v in ind.values() if v)
    print(f"wrote cycle.json ({ok}/{len(ind)} indicators)")


if __name__ == "__main__":
    main()
