"""Build monthlies.json -- Taiwan monthly revenue tracker for the AI supply chain.

Taiwan-listed companies must report monthly revenue by the ~10th of the
following month (MOPS). This script scrapes the official monthly summary
pages for both TWSE (sii) and TPEx (otc) boards, extracts the names below,
and computes MoM %, YoY %, and 3-month-average YoY.

Run from repo root: python fetch_tw_monthlies.py  ->  writes monthlies.json
Source: https://mopsov.twse.com.tw/nas/t21/{sii|otc}/t21sc03_{rocYear}_{month}_0.html
(legacy MOPS server -- the main mops.twse.com.tw dropped the /nas/t21 static files)
"""
import json
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
MONTHS_BACK = 60
UA = {"User-Agent": "Mozilla/5.0 (semis-dashboard monthly revenue tracker)"}

# code -> (name, group). All monthly reporters on TWSE/TPEx.
NAMES = {
    "2330": ("TSMC",        "Foundry"),
    "2317": ("Hon Hai",     "AI Server ODM"),
    "2382": ("Quanta",      "AI Server ODM"),
    "3231": ("Wistron",     "AI Server ODM"),
    "6669": ("Wiwynn",      "AI Server ODM"),
    "2356": ("Inventec",    "AI Server ODM"),
    "2324": ("Compal",      "AI Server ODM"),
    "4938": ("Pegatron",    "AI Server ODM"),
    "2376": ("Gigabyte",    "AI Server ODM"),
    "3706": ("MiTAC",       "AI Server ODM"),
    "2357": ("Asus",        "AI Server ODM"),
    "8210": ("Chenbro",     "Chassis / Rails"),
    "2059": ("King Slide",  "Chassis / Rails"),
    "2308": ("Delta",       "Power / Cooling"),
    "2301": ("Lite-On",     "Power / Cooling"),
    "3017": ("AVC",         "Power / Cooling"),
    "3324": ("Auras",       "Power / Cooling"),
    "2345": ("Accton",      "Networking / Components"),
    "3533": ("Lotes",       "Networking / Components"),
    "3665": ("BizLink",     "Networking / Components"),
}


def month_list(n):
    """Last n complete months as (year, month), oldest first."""
    now = datetime.now()
    y, m = now.year, now.month
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append((y, m))
    return list(reversed(out))


def fetch_month(year, month, board):
    """Return {code: revenue_thousands_twd} for one month/board."""
    roc = year - 1911
    url = f"https://mopsov.twse.com.tw/nas/t21/{board}/t21sc03_{roc}_{month}_0.html"
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200:
            return {}
        r.encoding = "big5"
        tables = pd.read_html(StringIO(r.text))
    except Exception as e:
        print(f"  {board} {year}-{month:02d}: {e}")
        return {}
    found = {}
    for tb in tables:
        if tb.shape[1] < 3:
            continue
        for _, row in tb.iterrows():
            code = str(row.iloc[0]).split(".")[0].strip()
            if code in NAMES and code not in found:
                try:
                    rev = float(str(row.iloc[2]).replace(",", ""))
                    found[code] = rev
                except Exception:
                    pass
    return found


def pct(a, b):
    try:
        if b:
            return round(100 * (a / b - 1), 1)
    except Exception:
        pass
    return None


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def ym_add(ym, k):
    y, m = int(ym[:4]), int(ym[5:7])
    m += k
    while m > 12: y, m = y + 1, m - 12
    while m < 1:  y, m = y - 1, m + 12
    return f"{y}-{m:02d}"


def q_of(ym):
    return (int(ym[5:7]) - 1) // 3 + 1


def q_months(year, q):
    return [f"{year}-{m:02d}" for m in range(3 * q - 2, 3 * q + 1)]


def q_seasonality(vals, q):
    """Median QoQ move into quarter q (vs quarter q-1), across all years in data."""
    ratios = []
    years = sorted({int(k[:4]) for k in vals})
    for y in years:
        cur = q_months(y, q)
        py, pq = (y - 1, 4) if q == 1 else (y, q - 1)
        prv = q_months(py, pq)
        if all(m in vals for m in cur) and all(m in vals for m in prv):
            a, b = sum(vals[m] for m in cur), sum(vals[m] for m in prv)
            if b:
                ratios.append(a / b)
    r = median(ratios)
    return round((r - 1) * 100, 1) if r else None


def month_seasonal_ratio(vals, month_num):
    """Median ratio of month m to month m-1 across years (for filling gaps)."""
    ratios = []
    for k in vals:
        if int(k[5:7]) == month_num:
            prev = ym_add(k, -1)
            if prev in vals and vals[prev]:
                ratios.append(vals[k] / vals[prev])
    return median(ratios)


def implied_quarter(vals, latest):
    """Implied YoY growth for the most recent quarter containing `latest`.
    3 months reported -> actual. 1-2 -> fill gaps with monthly seasonality.
    0 -> whole quarter from prior quarter x median QoQ seasonality."""
    y, q = int(latest[:4]), q_of(latest)
    months = q_months(y, q)
    have = [m for m in months if m in vals]
    est, method = {}, "actual"
    for m in months:
        if m in vals:
            est[m] = vals[m]
    if len(have) == 0:
        py, pq = (y - 1, 4) if q == 1 else (y, q - 1)
        prv = q_months(py, pq)
        if not all(m in vals for m in prv):
            return None
        r = q_seasonality(vals, q)
        if r is None:
            return None
        total = sum(vals[m] for m in prv) * (1 + r / 100)
        method = "seasonal"
    else:
        if len(have) < 3:
            method = "partial"
            for m in months:
                if m not in est:
                    prev = ym_add(m, -1)
                    base = est.get(prev) or vals.get(prev)
                    ratio = month_seasonal_ratio(vals, int(m[5:7]))
                    if base is None or ratio is None:
                        return None
                    est[m] = base * ratio
        total = sum(est[m] for m in months)
    prior_yr = [ym_add(m, -12) for m in months]
    if not all(m in vals for m in prior_yr):
        return None
    yoy = pct(total, sum(vals[m] for m in prior_yr))
    return {"q": f"Q{q}-{str(y)[2:]}", "yoy": yoy, "monthsIn": len(have), "method": method}


def next_release(latest):
    """Taiwan monthly revenue is due by the ~10th of the following month.
    Next unreported month = latest+1, released by 10th of latest+2."""
    rel = ym_add(latest, 2)
    return f"{rel}-10"


def main():
    # incremental mode: if we already have good history, only refresh the
    # last 3 months (12 requests) instead of the full 60-month backfill --
    # keeps us well under MOPS rate limits on daily runs.
    existing = {}
    out_path = ROOT / "monthlies.json"
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text())
            if len(prev.get("names", {})) >= 10:
                for c, x in prev["names"].items():
                    existing[c] = {k: v * 1000 for k, v in x["series"]}  # back to NT$k
        except Exception:
            pass
    incremental = bool(existing)
    months = month_list(3 if incremental else MONTHS_BACK)
    print(f"mode: {'incremental (3mo)' if incremental else 'full backfill (60mo)'}")

    series = {c: dict(existing.get(c, {})) for c in NAMES}   # code -> {"YYYY-MM": rev}
    for (y, m) in months:
        got = {}
        for board in ("sii", "otc"):
            got.update(fetch_month(y, m, board))
        key = f"{y}-{m:02d}"
        for c, v in got.items():
            series[c][key] = v
        print(f"{key}: {len(got)}/{len(NAMES)} names")
        time.sleep(1.0)                       # be polite to MOPS

    names_out = {}
    for c, (nm, grp) in NAMES.items():
        s = sorted(series[c].items())
        if not s:
            print(f"  WARNING no data for {c} {nm}")
            continue
        keys = [k for k, _ in s]
        vals = {k: v for k, v in s}
        yoy = []
        for k in keys:
            yr, mo = k.split("-")
            prior = f"{int(yr)-1}-{mo}"
            if prior in vals:
                yoy.append([k, pct(vals[k], vals[prior])])
        mom = pct(vals[keys[-1]], vals[keys[-2]]) if len(keys) > 1 else None
        # 3-month-average YoY: sum of last 3 months vs same 3 a year earlier
        t3 = None
        if len(keys) >= 3:
            last3 = keys[-3:]
            pri3 = [f"{int(k.split('-')[0])-1}-{k.split('-')[1]}" for k in last3]
            if all(p in vals for p in pri3):
                t3 = pct(sum(vals[k] for k in last3), sum(vals[p] for p in pri3))
        names_out[c] = {
            "n": nm, "group": grp,
            "series": [[k, round(vals[k] / 1000, 1)] for k in keys],   # NT$ millions
            "yoy": yoy,
            "latest": {"ym": keys[-1], "revM": round(vals[keys[-1]] / 1000, 1),
                       "mom": mom,
                       "yoy": yoy[-1][1] if yoy else None,
                       "t3mYoy": t3},
            "nextRelease": next_release(keys[-1]),
            "impliedQ": implied_quarter(vals, keys[-1]),
            "q2Season": q_seasonality(vals, 2),
        }

    # composite: aggregate AI Server ODM revenue YoY by month
    odm = [c for c, (n, g) in NAMES.items() if g == "AI Server ODM" and c in names_out]
    agg = {}
    for c in odm:
        for k, v in [(k, dict(names_out[c]["series"]).get(k)) for k, _ in names_out[c]["series"]]:
            agg.setdefault(k, {})[c] = v
    comp = []
    for k in sorted(agg):
        yr, mo = k.split("-")
        prior = f"{int(yr)-1}-{mo}"
        if prior in agg:
            cur_names = set(agg[k]) & set(agg[prior])
            if len(cur_names) >= 6:
                cur = sum(agg[k][c] for c in cur_names)
                old = sum(agg[prior][c] for c in cur_names)
                comp.append([k, pct(cur, old), len(cur_names)])

    # guard: never overwrite good data with an empty/failed scrape
    if len(names_out) < 10:
        print(f"ABORT: only {len(names_out)} names scraped (MOPS blocked/throttled?) "
              f"-- keeping existing monthlies.json untouched")
        return

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "TWSE/TPEx MOPS monthly revenue disclosures (NT$, company-level totals)",
        "names": names_out,
        "odmComposite": [[k, y] for k, y, _ in comp],
    }
    (ROOT / "monthlies.json").write_text(json.dumps(payload))
    print(f"wrote monthlies.json ({len(names_out)}/{len(NAMES)} names, "
          f"{len(comp)} composite points)")


if __name__ == "__main__":
    main()
