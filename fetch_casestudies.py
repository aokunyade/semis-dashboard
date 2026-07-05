"""Build casestudies.json -- deep-dive study library for the Semis Cockpit.

Two sections:
  1. corrections  - index charts of the major market drawdowns in history
  2. cycles       - past technology cycles (mainframe, PC, mobile, cloud, COVID):
                    index look + 6 winners + 6 losers + PM bullets on the
                    inflection, the peak/sell signal, and the short-cover tell.

Delisted names with no retrievable price history (DEC, Compaq, Wang, ...) are
kept as narrative cards so the study set stays complete.

Run from repo root: python fetch_casestudies.py  ->  writes casestudies.json
Data: Yahoo Finance via yfinance. Bullets are static, editable below.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# 1. MAJOR CORRECTIONS -- "the index look"
# --------------------------------------------------------------------------- #
CORRECTIONS = [
 dict(id="crash1929", sym="^GSPC", name="1929-32 Great Crash", label="S&P Composite",
      start="1928-01-01", end="1938-01-01", freq="ME", bullets=[
      "Driver in: a decade of margin-fueled retail leverage (10% margin), broker call loans and a capex/utilities bubble; the tape topped Sep-1929 while rails and steel output were already rolling over -- breadth died months before price.",
      "Sell tell at the peak: rampant leverage plus the first failed rally (Oct '29 bounce died below the high) -- in a leverage unwind the first -30% is not the buy; the market fell another ~75% into Jul-1932.",
      "Cover tell at the trough: 1932 bottom came on total capitulation -- volume dried up, stocks below net cash, dividend yields >10% -- and the policy regime change (1933 devaluation/bank holiday) was the durable turn."]),
 dict(id="bear1973", sym="^GSPC", name="1973-74 Nifty Fifty / Oil Shock", label="S&P 500",
      start="1970-01-01", end="1979-01-01", freq="ME", bullets=[
      "Driver in: 'one-decision' quality growth (Nifty Fifty at 40-80x) met an oil embargo, 12% inflation and a Fed forced to tighten into a recession -- multiple compression did the damage even where earnings held.",
      "Sell tell: when the leadership itself is the valuation problem, rotation can't save you -- the Fifty fell 60-90% (Polaroid -91%, Disney -86%); the tell was paying any price for 'never sell' assets.",
      "Cover tell: Dec-1974 trough came with single-digit S&P P/E and peak pessimism while inflation was still high -- the market bottomed on valuation, not on good news."]),
 dict(id="crash1987", sym="^GSPC", name="1987 Black Monday", label="S&P 500",
      start="1986-01-01", end="1990-01-01", freq="W", bullets=[
      "Driver in: +40% YTD melt-up into August on falling dollar/rate worries, with portfolio insurance (systematic selling of futures into weakness) embedding a doom loop nobody had stress-tested.",
      "Sell tell: rates -- the 10y went from 7% to >10% during 1987 while equities made new highs; when bonds and stocks diverge that hard, own the disagreement, don't fight it. -20.5% in one day settled it.",
      "Cover tell: mechanical, not fundamental, crashes recover fast -- earnings never fell, the Fed flooded liquidity, and the index was at new highs within 2 years. Distinguish market-structure events from earnings events."]),
 dict(id="bear1990", sym="^GSPC", name="1990 Gulf War / S&L", label="S&P 500",
      start="1989-01-01", end="1993-01-01", freq="W", bullets=[
      "Driver in: oil doubled on the Kuwait invasion into an economy already soft from the S&L credit crunch -- a classic exogenous-shock-meets-late-cycle setup.",
      "Sell tell: credit led equities -- bank stocks and high yield were breaking down well before the index; when financials diverge, respect it.",
      "Cover tell: the -20% trough resolved when the Fed cut and the war outcome de-risked (Jan-91) -- geopolitical bears end on certainty, not on peace."]),
 dict(id="ltcm1998", sym="^GSPC", name="1998 Asia / LTCM", label="S&P 500",
      start="1997-01-01", end="2000-01-01", freq="W", bullets=[
      "Driver in: EM contagion (Thailand->Korea->Russia default) blew up a levered convergence fund (LTCM) big enough to threaten the street -- a positioning unwind, not a US earnings event.",
      "Sell tell: spread products cracked months before equities -- swap spreads and EM debt were screaming while the S&P made highs in July.",
      "Cover tell: -19% and reversed on three Fed cuts in six weeks; when the shock is leverage/positioning and the Fed moves, the V is violent -- the Nasdaq doubled in the following 15 months."]),
 dict(id="dotcom2000", sym="^IXIC", name="2000-02 Dot-com Bust", label="Nasdaq Composite",
      start="1995-01-01", end="2006-01-01", freq="ME", bullets=[
      "Driver in: genuine platform shift (internet) financed indiscriminately -- 1999: +86% Nasdaq, 300+ IPOs, companies valued on eyeballs; capex (telecom fiber) ran 3-4x ahead of demand.",
      "Sell tell at the peak: supply -- insider lockup expiries and secondary issuance flooded out in Q1-2000 while the 'picks and shovels' (CSCO, NT) guided down on carrier capex; when the arms dealers crack, the war is over.",
      "Cover tell: -78% over 2.5 years with three +30% bear rallies -- shorts covered on capitulation valuation (real FCF yields at profitable survivors) in Oct-02, not on the first bounce. Survivors (AMZN -94%) still worked from the ashes."]),
 dict(id="gfc2008", sym="^GSPC", name="2008-09 Global Financial Crisis", label="S&P 500",
      start="2006-01-01", end="2014-01-01", freq="W", bullets=[
      "Driver in: housing credit leverage sat inside the banking system itself -- when collateral (homes) fell, the intermediaries broke; Bear/Lehman turned a credit cycle into a funding run.",
      "Sell tell: credit again -- 2y swap spreads, ABX and financial CDS deteriorated for 12 months while the S&P made a marginal new high in Oct-07. Equities are the last asset class to get the memo.",
      "Cover tell: the Mar-09 bottom was policy regime change (TARP deployed, Fed QE, mark-to-market relief) at 666 on the S&P -- covering shorts on the policy pivot beat covering on price; semis (SOX) bottomed Nov-08, months early, as orders troughed."]),
 dict(id="q42018", sym="^GSPC", name="2018 Q4 Rate/Trade Scare", label="S&P 500",
      start="2018-01-01", end="2020-01-01", freq="W", bullets=[
      "Driver in: Fed hiking on 'autopilot' into a trade war and decelerating global PMIs -- QT plus tariffs compressed multiples 20% in a quarter with no recession.",
      "Sell tell: semis led down -- the SOX peaked in March on memory rolling over (MU, Samsung cuts) two quarters before the index; semis are the cycle's canary, which is the point of this dashboard.",
      "Cover tell: Powell's Jan-4 'patient' pivot was the all-clear; positioning washouts driven by policy fear end the day the policy changes."]),
 dict(id="covid2020", sym="^GSPC", name="2020 COVID Crash", label="S&P 500",
      start="2019-06-01", end="2022-01-01", freq="W", bullets=[
      "Driver in: a true exogenous stop -- fastest -34% in history (23 sessions) as the economy was administratively closed; correlation went to 1, everything was a source of funds.",
      "Sell tell: none available in price beforehand -- the lesson is sizing and convexity: tails are why you never run max gross into complacent vol lows (VIX 12 in Jan-20).",
      "Cover tell: Mar-23 bottom = unlimited QE + fiscal at scale, before the virus news improved. Policy > epidemiology. Tech/semis then re-rated on pulled-forward digitization -- the crash was the entry to the next cycle."]),
 dict(id="rates2022", sym="^IXIC", name="2022 Rate Shock", label="Nasdaq Composite",
      start="2021-01-01", end="2024-07-01", freq="W", bullets=[
      "Driver in: 9% CPI ended the free-money regime -- the discount rate went from 0 to 5% and long-duration growth (unprofitable tech -70/80%) bore the math; semis added an inventory bust on top (SOX -46%).",
      "Sell tell at the peak: the speculative fringe broke first -- SPACs, ARKK, crypto peaked Feb-21, a full 10 months before the index; when the junk leads down and breadth narrows to megacap, the clock is running.",
      "Cover tell: Oct-22 trough = peak CPI prints behind, semis had already guided down (MU cut capex Sep-22 = classic memory-trough signal), and the first 'slower hikes' Fed language. The AI cycle was born in that trough (ChatGPT: Nov-22)."]),
]

# --------------------------------------------------------------------------- #
# 2. TECHNOLOGY CYCLES -- winners vs. losers
#    nar=True cards have no retrievable listed history (delisted/acquired).
# --------------------------------------------------------------------------- #
CYCLES = [
 dict(id="mainframe", name="Mainframe Era", period="1962-1985", index=("^GSPC", "S&P 500"),
      start="1962-01-01", end="1986-01-01",
      winners=[
        dict(t="IBM", sym="IBM", n="IBM", note="~70% share; S/360 ($5B bet, 1964) created the compatible-platform franchise; the safe monopoly of the era."),
        dict(t="TXN", sym="TXN", n="Texas Instruments", note="Semiconductor arms dealer to every computer maker; learning-curve pricing pioneer."),
        dict(t="HPQ", sym="HPQ", n="Hewlett-Packard", note="Instruments -> minis -> calculators; compounded through the whole era."),
        dict(t="MSI", sym="MSI", n="Motorola", note="Semis + communications; supplied the microprocessor insurgency (68000)."),
        dict(t="INTC", sym="INTC", n="Intel", note="b. 1968 in memory; the 1103 DRAM then the microprocessor -- the era's seed of the next era."),
        dict(t="DEC", sym=None, nar=True, n="Digital Equipment", note="THE growth stock of the era: minicomputers undercut IBM 10x on price; from $70K 1957 startup to #2 in the industry by the 80s. (Delisted -- bought by Compaq '98.)"),
      ],
      losers=[
        dict(t="BGH", sym=None, nar=True, n="Burroughs", note="One of the 'BUNCH'; strong in banking; never escaped IBM's gravity; merged with Sperry into Unisys (1986) -- a shrink-to-merge endgame."),
        dict(t="SPY", sym=None, nar=True, n="Sperry Rand (UNIVAC)", note="First-mover in commercial computing (UNIVAC I, 1951) -- lost the market to IBM's sales force and compatibility; first-mover advantage is not distribution."),
        dict(t="CDC", sym=None, nar=True, n="Control Data", note="Supercomputer star of the 60s (a 100x stock 1958-68!) -- peaked when it diversified into services/finance; broke up by the 80s. Sell the pivot."),
        dict(t="NCR", sym=None, nar=True, n="NCR", note="Cash registers -> computers too slowly; commoditized; absorbed by AT&T (1991) at a fraction of former relevance."),
        dict(t="HON", sym=None, nar=True, n="Honeywell (computers)", note="Perennial #2 strategy ('the other computer company') -- exited computing entirely by 1991. #2 in a winner-take-most platform market is a losing hand."),
        dict(t="WANG", sym=None, nar=True, n="Wang Labs", note="Word-processing king of the late 70s; $3B revenue; refused the PC/generalization wave; Chapter 11 in 1992. Product-cycle companies die on the next cycle."),
      ],
      bullets=[
      "Inflection: the S/360 compatible platform (1964) turned computing from custom projects into an installed-base annuity -- the buy signal was lock-in economics (leases, software switching costs), not box shipments.",
      "Sell at the peak: IBM peaked as a relative asset when the disruptors' unit economics crossed (minis at 1/10th the price, then PCs) -- ~1985 IBM was still reporting record earnings while its franchise decayed; sell platform monopolies when the NEXT platform's cost curve undercuts them, not when their EPS breaks.",
      "Short/cover: the BUNCH shorts worked for a decade -- structural share donors in a winner-take-most market don't mean-revert; cover only on liquidation/merger events (Unisys 1986), never on 'cheap'."]),

 dict(id="pc", name="PC Era", period="1981-2000", index=("^IXIC", "Nasdaq Composite"),
      start="1981-01-01", end="2001-01-01",
      winners=[
        dict(t="MSFT", sym="MSFT", n="Microsoft", note="The OS toll booth -- captured the industry's economics with ~0 capital intensity."),
        dict(t="INTC", sym="INTC", n="Intel", note="The other half of Wintel; 'Intel Inside' turned a component into a brand with monopoly margins."),
        dict(t="CSCO", sym="CSCO", n="Cisco", note="PCs needed networks; the picks-and-shovels of client/server -- 1,000x from '90 IPO to '00 peak."),
        dict(t="ORCL", sym="ORCL", n="Oracle", note="Client/server database standard; software attach to the hardware boom."),
        dict(t="HPQ", sym="HPQ", n="Hewlett-Packard", note="Rode PCs + the printer ink annuity."),
        dict(t="DELL", sym=None, nar=True, n="Dell", note="Direct model + negative working capital = the era's best business model; roughly +90,000% from the '88 IPO to 2000. (Original listing history lost to the 2013 LBO.)"),
      ],
      losers=[
        dict(t="IBM", sym="IBM", n="IBM", note="Created the PC, gave away the economics (MSFT/INTC); earnings collapsed 1991-93 -- the canonical value-trap decade."),
        dict(t="AAPL", sym="AAPL", n="Apple (in this era)", note="Closed model lost to Wintel; 90 days from bankruptcy in 1997 -- proof that era losers can seed the next era."),
        dict(t="UIS", sym="UIS", n="Unisys", note="The merged mainframe also-rans; two melting ice cubes make a bigger ice cube."),
        dict(t="DEC", sym=None, nar=True, n="Digital Equipment", note="Last era's growth star: 'no reason anyone would want a computer in their home' (Olsen, '77); peak $ in '87, sold to Compaq '98. Winners of cycle N are the shorts of cycle N+1."),
        dict(t="CPQ", sym=None, nar=True, n="Compaq", note="Early PC winner (fastest to $1B in US history) -- commoditized by Dell's direct model; margin structure died before the stock; absorbed by HP (2002)."),
        dict(t="CBM", sym=None, nar=True, n="Commodore", note="Outsold everyone in units (C64) at the low end -- no ecosystem, no margins; bankrupt 1994. Unit share without profit share is a trap."),
      ],
      bullets=[
      "Inflection: buy signal was the 1981 IBM PC legitimizing the category + the clone/Wintel standard (1984-86) -- standards, not boxes, carried the economics; the OS and the CPU took ~all industry profit within a decade.",
      "Sell at the peak: box makers peaked when growth shifted from 'who wins share' to 'category price deflation' (mid-90s: sub-$1,000 PCs); the sell tell was gross margin structure, visible quarters before EPS -- Compaq's 1991 margin crash previewed everyone's fate.",
      "Short/cover: IBM was the great slow short of 1987-93 (fat, high-multiple incumbent + collapsing franchise) -- but cover on regime change: Gerstner 1993 (new CEO + dividend cut + services pivot) marked the exact turn. Manage structural shorts around catalysts, not valuation."]),

 dict(id="mobile", name="Mobile / Smartphone Era", period="2005-2016", index=("^IXIC", "Nasdaq Composite"),
      start="2005-01-01", end="2017-01-01",
      winners=[
        dict(t="AAPL", sym="AAPL", n="Apple", note="Redefined the category (2007) and took >80% of industry profit by 2012."),
        dict(t="QCOM", sym="QCOM", n="Qualcomm", note="The royalty toll booth -- licensed every smartphone regardless of who won."),
        dict(t="AVGO", sym="AVGO", n="Broadcom (Avago)", note="RF content per phone compounding + serial consolidation."),
        dict(t="SWKS", sym="SWKS", n="Skyworks", note="Pure-play RF content story: more bands = more $ content every generation."),
        dict(t="TSM", sym="TSM", n="TSMC", note="Every mobile SoC needed leading-edge foundry; the neutral arms dealer."),
        dict(t="SSNLF", sym="005930.KS", n="Samsung Electronics", note="Only integrated player to win -- components (memory/AP/display) hedged the handset fight. (Local ccy.)"),
      ],
      losers=[
        dict(t="NOK", sym="NOK", n="Nokia", note="40% global share in 2007 -> exited handsets 2013; software (Symbian) was the kill shot, not hardware."),
        dict(t="BB", sym="BB", n="BlackBerry", note="Enterprise lock-in was no moat vs. a better consumer product; peak $83B cap (2008) -> sub-$5B."),
        dict(t="MSI", sym="MSI", n="Motorola", note="RAZR one-hit-wonder; handset unit spun and sold to Google mostly for patents."),
        dict(t="GRMN", sym="GRMN", n="Garmin", note="The adjacency kill: the smartphone absorbed the PND category whole. -70% 2007-09."),
        dict(t="HTC", sym="2498.TW", n="HTC", note="First Android flagship maker; no silicon, no ecosystem, no brand moat -- peaked 2011, -95% after. (Local ccy.)"),
        dict(t="ERIC", sym="ERIC", n="Ericsson", note="Handset exit (Sony JV) + infrastructure commoditization by Huawei; the era's growth went around it."),
      ],
      bullets=[
      "Inflection: iPhone (2007) + App Store (2008) turned phones into computing platforms -- buy signal was attach economics: content-per-device (RF, foundry wafers, royalties) growing faster than units. The suppliers (QCOM, AVGO, SWKS, TSM) were buyable with less product risk than the handset fight itself.",
      "Sell at the peak: unit growth peaked ~2015 (smartphone penetration saturated) -- sell tell for the content names was deceleration in $-content growth + customer concentration risk repricing (SWKS/QCOM 2015-16 when Apple units flattened); in platform eras, sell the component names when the device S-curve flattens, before the ecosystem names.",
      "Short/cover: incumbent handset shorts (NOK, BB) worked on the software/ecosystem gap, and the cover signal was capitulation-exit events (Nokia selling to MSFT 2013, BB going enterprise-software) -- by then the equity had already lost 90%+; the money was made in years 1-3 of denial, when 'cheap' and 'installed base' were the bull case."]),

 dict(id="cloud", name="Cloud Era", period="2010-2021", index=("^IXIC", "Nasdaq Composite"),
      start="2010-01-01", end="2022-01-01",
      winners=[
        dict(t="AMZN", sym="AMZN", n="Amazon (AWS)", note="Invented the category; retail cash funded a software-margin monopoly nobody modeled until 2015 disclosure."),
        dict(t="MSFT", sym="MSFT", n="Microsoft", note="The great incumbent transition: Nadella (2014) pivoted the installed base to Azure/SaaS -- multiple went 10x->35x."),
        dict(t="CRM", sym="CRM", n="Salesforce", note="Proved the SaaS model at scale; the template every software company re-rated on."),
        dict(t="NOW", sym="NOW", n="ServiceNow", note="Pure-play SaaS compounder -- 20%+ growth for a decade straight."),
        dict(t="ADBE", sym="ADBE", n="Adobe", note="The license->subscription conversion playbook: revenue dipped, LTV soared, stock 10x'd."),
        dict(t="NVDA", sym="NVDA", n="NVIDIA", note="GPUs became the cloud's compute engine (ML) -- the cloud era's semis winner and the bridge to the AI era."),
      ],
      losers=[
        dict(t="IBM", sym="IBM", n="IBM", note="'Cloud-washed' legacy services for a decade; revenue declined 2012-2020 while buying back stock -- financial engineering vs. secular decline loses."),
        dict(t="ORCL", sym="ORCL", n="Oracle (2010s)", note="Denied cloud ('gibberish' -- Ellison 2008), lost a decade of relative performance defending license margins."),
        dict(t="TDC", sym="TDC", n="Teradata", note="On-prem data warehouse -- the exact workload Snowflake/Redshift ate. -75% from 2012 peak."),
        dict(t="HPE", sym="HPE", n="HP Enterprise", note="Selling servers to companies that were moving compute to clouds that build their own."),
        dict(t="DXC", sym="DXC", n="DXC Technology", note="Legacy IT outsourcing rollup -- shrinking pie, leverage, serial restructuring."),
        dict(t="NTAP", sym="NTAP", n="NetApp", note="On-prem storage: survived but ceded the growth; a decade of flat revenue in a 30%-CAGR category."),
      ],
      bullets=[
      "Inflection: buy signal was unit economics disclosure -- AWS's first segment print (Apr-2015: 17% margin, 50% growth) repriced the whole complex; before that the tell was capex: hyperscaler capex inflected 2013-15 while enterprise IT spend stalled. Follow the capex, it IS the cycle (same signal this dashboard tracks).",
      "Sell at the peak: the era's blowoff was 2020-21 -- sell tell was valuation regime dependence: SaaS at 30-40x SALES only works at 0% rates; when the rate regime turned (2021), the highest-multiple cohort fell 70-80% regardless of execution. Sell the multiple, not the company.",
      "Short/cover: legacy IT shorts (IBM, TDC, DXC) were grinding structural donors -- cover on genuine business-model regime change only (IBM: Kyndryl spin + AI narrative 2023 re-rated it; ORCL: OCI/AI capex turned it 2023) -- 'new CEO + real product cycle' is the cover signal, dividend yield is not."]),

 dict(id="covid", name="COVID Boom & Bust", period="2019-2023", index=("^IXIC", "Nasdaq Composite"),
      start="2019-01-01", end="2024-01-01",
      winners=[
        dict(t="NVDA", sym="NVDA", n="NVIDIA", note="Gaming/datacenter pull-forward, -66% in 2022 inventory bust, then the AI supercycle -- the full cycle in one chart."),
        dict(t="AAPL", sym="AAPL", n="Apple", note="Stay-at-home device demand + services; the quality compounder path through the whole event."),
        dict(t="MSFT", sym="MSFT", n="Microsoft", note="Teams/Azure -- the enterprise digitization checkbook."),
        dict(t="AMD", sym="AMD", n="AMD", note="PC/console/server demand surge + share gains vs Intel; held most of the re-rate."),
        dict(t="TSLA", sym="TSLA", n="Tesla", note="The liquidity era's defining momentum asset -- 15x in 18 months; also the regime-change casualty (-73% in 2022).") ,
        dict(t="SHOP", sym="SHOP", n="Shopify", note="E-commerce pull-forward poster child: 10x up, -85% down, then a real business re-emerged -- separates COMPANY from PULL-FORWARD."),
      ],
      losers=[
        dict(t="ZM", sym="ZM", n="Zoom", note="Peak cap > ExxonMobil on a feature; TAM pull-forward priced as TAM expansion. -90%."),
        dict(t="PTON", sym="PTON", n="Peloton", note="Hardware demand spike modeled as a subscription annuity; inventory + churn killed it. -98%."),
        dict(t="DOCU", sym="DOCU", n="DocuSign", note="Real product, one-time adoption step-function priced as permanent growth. -85%."),
        dict(t="TDOC", sym="TDOC", n="Teladoc", note="Peak-cycle M&A (Livongo, $18.5B) at the top -- goodwill writedowns did the accounting confession later."),
        dict(t="ROKU", sym="ROKU", n="Roku", note="Streaming hours pulled forward + ad market turned; -90% from peak."),
        dict(t="NFLX", sym="NFLX", n="Netflix (2021-22)", note="The subscriber miss (Apr-22) that repriced the whole 'growth at any price' complex in one print; -75% peak-to-trough, then recovered on the ads/paid-sharing model turn."),
      ],
      bullets=[
      "Inflection: the buy was policy + behavior change (Mar-Apr 2020): unlimited QE plus a forced digitization experiment -- the tell for sizing up was fiscal transfers hitting consumer accounts while the entire sell side modeled a demand collapse.",
      "Sell at the peak: distinguish pull-forward from TAM change -- the sell tell was decelerating cohort/usage data against accelerating consensus (ZM churn, PTON engagement, 2H-21) plus the speculative tape breaking first (ARKK/SPACs peaked Feb-21, 10 months before the index). When the beneficiaries start buying growth at the top (TDOC/Livongo), the organic story is over.",
      "Short/cover: COVID-darling shorts paid for 18 months straight -- cover tell was the accounting confession cycle completing (writedowns, guidance kitchen-sinks, mgmt turnover: PTON new CEO Feb-22, kitchen-sink guides through 2022) and real FCF appearing at the survivors (NFLX ads pivot). Bust survivors with a second act (SHOP, NFLX) became the next longs -- same as AMZN 2002."]),
]

# --------------------------------------------------------------------------- #

def fetch_series(sym, start, end, freq="ME"):
    """Monthly (ME) or weekly (W) closes -> [[YYYY-MM(-DD), px], ...]"""
    try:
        h = yf.download(sym, start=start, end=end, interval="1d",
                        auto_adjust=True, progress=False)
        if h is None or h.empty:
            return None
        px = h["Close"]
        if isinstance(px, pd.DataFrame):
            px = px.iloc[:, 0]
        px = px.dropna()
        r = px.resample(freq).last().dropna()
        fmt = "%Y-%m" if freq == "ME" else "%Y-%m-%d"
        return [[d.strftime(fmt), round(float(v), 2)] for d, v in r.items()]
    except Exception as e:
        print(f"  {sym}: {e}")
        return None


def drawdown(series):
    if not series:
        return None
    peak, trough, dd = series[0][1], series[0][1], 0.0
    pk_d = tr_d = series[0][0]
    run_pk, run_pk_d = series[0][1], series[0][0]
    for d, v in series:
        if v > run_pk:
            run_pk, run_pk_d = v, d
        cur = v / run_pk - 1
        if cur < dd:
            dd, peak, pk_d, trough, tr_d = cur, run_pk, run_pk_d, v, d
    return {"dd": round(dd * 100, 1), "peakDate": pk_d, "troughDate": tr_d}


def total_return(series):
    if not series or series[0][1] == 0:
        return None
    return round((series[-1][1] / series[0][1] - 1) * 100, 1)


def build_name(cfg, start, end):
    out = {k: cfg[k] for k in ("t", "n", "note") if k in cfg}
    if cfg.get("nar") or not cfg.get("sym"):
        out["nar"] = True
        return out
    s = fetch_series(cfg["sym"], start, end, "ME")
    if s:
        out["series"] = s
        out["ret"] = total_return(s)
        out["dd"] = drawdown(s)
    else:
        out["nar"] = True
        out["note"] = out.get("note", "") + " (price history unavailable)"
    return out


def main():
    corrections = []
    for c in CORRECTIONS:
        print("correction:", c["name"])
        s = fetch_series(c["sym"], c["start"], c["end"], c["freq"])
        corrections.append({"id": c["id"], "name": c["name"], "label": c["label"],
                            "series": s, "dd": drawdown(s), "bullets": c["bullets"]})
    cycles = []
    for cy in CYCLES:
        print("cycle:", cy["name"])
        idx = fetch_series(cy["index"][0], cy["start"], cy["end"], "ME")
        cycles.append({
            "id": cy["id"], "name": cy["name"], "period": cy["period"],
            "index": {"label": cy["index"][1], "series": idx, "dd": drawdown(idx)},
            "winners": [build_name(w, cy["start"], cy["end"]) for w in cy["winners"]],
            "losers":  [build_name(l, cy["start"], cy["end"]) for l in cy["losers"]],
            "bullets": cy["bullets"]})
    payload = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "corrections": corrections, "cycles": cycles}
    (ROOT / "casestudies.json").write_text(json.dumps(payload))
    print("wrote casestudies.json")


if __name__ == "__main__":
    main()
