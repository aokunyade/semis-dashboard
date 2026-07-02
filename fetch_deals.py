"""Track signed neocloud compute deals -> deals.json

Two layers:
  1. CURATED  - hand-maintained list of confirmed signed deals (edit below).
  2. SCANNED  - daily Google News RSS sweep for deal headlines mentioning
                neocloud providers, rolling 92-day window, $-amounts parsed
                from titles. Curated entries never expire; scanned ones roll off.

Run from repo root: python fetch_deals.py  ->  writes deals.json
"""
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import requests

WINDOW_DAYS = 92

# ---- curated signed deals (edit me) -----------------------------------------
CURATED = [
    {"date": "2026-06", "provider": "SpaceX (Colossus)", "customer": "Google",
     "valueB": 29.4, "term": "Oct 2026 - Jun 2029 ($920M/mo)",
     "note": "~110k NVIDIA GPUs at Colossus, Memphis"},
    {"date": "2026-05", "provider": "xAI (Colossus 1)", "customer": "Anthropic",
     "valueB": 45.0, "term": "Through May 2029 ($1.25B/mo)",
     "note": "Full buyout of Colossus 1 capacity, ~300MW"},
    {"date": "2026-04", "provider": "Nebius", "customer": "Meta",
     "valueB": 27.0, "term": "5 years", "note": "Up to $27B"},
    {"date": "2026-04", "provider": "CoreWeave", "customer": "Meta",
     "valueB": 21.0, "term": "Through Dec 2032",
     "note": "Expanded from initial $14B commitment"},
    {"date": "2026-04", "provider": "Cerebras", "customer": "OpenAI",
     "valueB": 10.0, "term": "Through 2028",
     "note": "750MW ultra-low-latency inference, >$10B"},
]

PROVIDERS = ["coreweave", "nebius", "lambda", "crusoe", "iren", "fluidstack",
             "applied digital", "together ai", "vast data", "cerebras",
             "neocloud", "nscale", "voltage park", "colossus", "xai"]
DEAL_WORDS = ["deal", "contract", "agreement", "signs", "signed", "commits",
              "partnership", "capacity", "buys", "expands", "order"]

RSS = ("https://news.google.com/rss/search?q="
       "(coreweave+OR+nebius+OR+neocloud+OR+fluidstack+OR+iren+OR+crusoe+OR+"
       "%22applied+digital%22+OR+%22lambda%22+OR+nscale)+"
       "(deal+OR+contract+OR+agreement+OR+signs)+when:92d"
       "&hl=en-US&gl=US&ceid=US:en")

AMT = re.compile(r"\$\s?(\d+(?:\.\d+)?)\s*(billion|bn|b\b|million|m\b)", re.I)


def parse_amount(text):
    m = AMT.search(text)
    if not m:
        return None
    v = float(m.group(1))
    return round(v if m.group(2).lower().startswith(("b",)) or "billion" in m.group(2).lower()
                 else v / 1000, 2)


def scan():
    r = requests.get(RSS, timeout=30, headers={"User-Agent": "Mozilla/5.0 (semis-dashboard)"})
    root = ET.fromstring(r.content)
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    out, seen = [], set()
    for it in root.findall(".//item"):
        title = (it.findtext("title") or "").strip()
        link = it.findtext("link") or ""
        low = title.lower()
        if not any(p in low for p in PROVIDERS):
            continue
        if not any(w in low for w in DEAL_WORDS):
            continue
        try:
            pub = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            continue
        if pub < cutoff:
            continue
        key = re.sub(r"\W+", "", low)[:60]
        if key in seen:
            continue
        seen.add(key)
        prov = next((p for p in PROVIDERS if p in low), "")
        out.append({"d": pub.strftime("%Y-%m-%d"),
                    "t": re.sub(r"\s+-\s+[^-]+$", "", title),
                    "u": link, "amt": parse_amount(title), "prov": prov.title()})
    out.sort(key=lambda x: x["d"], reverse=True)
    return out[:40]


def main():
    try:
        scanned = scan()
    except Exception as e:
        print(f"scan failed: {e}")
        scanned = []
    payload = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "windowDays": WINDOW_DAYS, "curated": CURATED, "scanned": scanned}
    with open("deals.json", "w") as f:
        json.dump(payload, f)
    print(f"wrote deals.json ({len(CURATED)} curated, {len(scanned)} scanned)")


if __name__ == "__main__":
    main()
