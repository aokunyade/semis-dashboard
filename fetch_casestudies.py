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
        dict(t="IBM", sym="IBM", n="IBM", mcap="'62 ~$14B -> '85 ~$95B",
             desc="Mainframe systems, leased and serviced end-to-end",
             seg="computing ~35% of rev (early 60s) -> ~85% ('85)",
             note="~70% share; S/360 ($5B bet, 1964) created the compatible-platform franchise; the safe monopoly of the era."),
        dict(t="TXN", sym="TXN", n="Texas Instruments", mcap="'72 ~$1.5B -> '85 ~$2.5B",
             desc="Semiconductors + defense electronics",
             seg="semis ~40% of rev ('72) -> ~55% ('85)",
             note="Semiconductor arms dealer to every computer maker; learning-curve pricing pioneer."),
        dict(t="HPQ", sym="HPQ", n="Hewlett-Packard", mcap="'65 ~$0.5B -> '85 ~$8B",
             desc="Test & measurement instruments -> minicomputers and calculators",
             seg="computing ~5% of rev ('65) -> ~50% ('85)",
             note="Instruments -> minis -> calculators; compounded through the whole era."),
        dict(t="MSI", sym="MSI", n="Motorola", mcap="'77 ~$1.5B -> '85 ~$4B",
             desc="Two-way radio / communications + a semiconductor arm",
             seg="semis ~25% of rev through the era; supplied the 68000 CPU",
             note="Semis + communications; supplied the microprocessor insurgency (68000)."),
        dict(t="INTC", sym="INTC", n="Intel", mcap="'71 IPO ~$0.06B -> '85 ~$4B",
             desc="Memory chips -> microprocessors",
             seg="DRAM ~90% of rev ('72) -> microprocessors ~55% ('85, exited DRAM)",
             note="b. 1968 in memory; the 1103 DRAM then the microprocessor -- the era's seed of the next era."),
        dict(t="DEC", sym=None, nar=True, n="Digital Equipment", mcap="'66 IPO ~$0.2B -> peak '87 ~$26B",
             desc="Minicomputers (PDP, then VAX)",
             seg="minis ~100% of rev; $14M ('60s) -> ~$7B ('85)",
             note="THE growth stock of the era: minicomputers undercut IBM 10x on price; from $70K 1957 startup to #2 in the industry by the 80s. (Delisted -- bought by Compaq '98.)"),
      ],
      losers=[
        dict(t="BGH", sym=None, nar=True, n="Burroughs",
             desc="Bank accounting machines -> mainframes",
             seg="computing ~60% of rev but ~5% industry share vs IBM's ~70%",
             note="One of the 'BUNCH'; strong in banking; never escaped IBM's gravity; merged with Sperry into Unisys (1986) -- a shrink-to-merge endgame."),
        dict(t="SPY", sym=None, nar=True, n="Sperry Rand (UNIVAC)",
             desc="UNIVAC mainframes + defense electronics",
             seg="computing ~50% of rev; share stuck below 10% the whole era",
             note="First-mover in commercial computing (UNIVAC I, 1951) -- lost the market to IBM's sales force and compatibility; first-mover advantage is not distribution."),
        dict(t="CDC", sym=None, nar=True, n="Control Data",
             desc="Supercomputers -> diversified into services/finance",
             seg="hardware ~80% of rev ('68) -> <40% ('85) after the pivot",
             note="Supercomputer star of the 60s (a 100x stock 1958-68!) -- peaked when it diversified into services/finance; broke up by the 80s. Sell the pivot."),
        dict(t="NCR", sym=None, nar=True, n="NCR",
             desc="Cash registers -> computers, too slowly",
             seg="computing <30% of rev until the 80s -- the shift came a decade late",
             note="Cash registers -> computers too slowly; commoditized; absorbed by AT&T (1991) at a fraction of former relevance."),
        dict(t="HON", sym=None, nar=True, n="Honeywell (computers)",
             desc="Controls conglomerate with computing as a side bet",
             seg="computing ~15-20% of rev -- never core, never scaled",
             note="Perennial #2 strategy ('the other computer company') -- exited computing entirely by 1991. #2 in a winner-take-most platform market is a losing hand."),
        dict(t="WANG", sym=None, nar=True, n="Wang Labs",
             desc="Dedicated word-processing machines / office minis",
             seg="word processing ~70%+ of rev at peak -- a single product cycle",
             note="Word-processing king of the late 70s; $3B revenue; refused the PC/generalization wave; Chapter 11 in 1992. Product-cycle companies die on the next cycle."),
      ],
      bullets=[
      "Inflection: the S/360 compatible platform (1964) -- System/360 was IBM's first FAMILY of mainframes that all ran the same software, so a customer could move up to a bigger machine without rewriting a line of code -- turned computing from custom projects into an installed-base annuity; the buy signal was lock-in economics (leases, software switching costs), not box shipments.",
      "Sell at the peak: IBM peaked as a relative asset when the disruptors' unit economics crossed (minis at 1/10th the price, then PCs) -- ~1985 IBM was still reporting record earnings while its franchise decayed; sell platform monopolies when the NEXT platform's cost curve undercuts them, not when their EPS breaks.",
      "Short/cover: the BUNCH shorts worked for a decade -- structural share donors in a winner-take-most market don't mean-revert; cover only on liquidation/merger events (Unisys 1986), never on 'cheap'.",
      "LESSON OF THE ERA: switching costs are the profit pool. IBM's money was never the box -- it was the lease plus software lock-in on an installed base too painful to leave. Competitors with better or cheaper hardware (the BUNCH) never mattered because the customer's real cost of leaving was rewriting everything."]),

 dict(id="pc", name="PC Era", period="1981-2000", index=("^IXIC", "Nasdaq Composite"),
      start="1981-01-01", end="2001-01-01",
      winners=[
        dict(t="MSFT", sym="MSFT", n="Microsoft", mcap="'86 IPO ~$0.8B -> '00 ~$600B",
             desc="PC software: the OS (DOS/Windows) + Office apps",
             seg="PC software ~100% of rev; $198M ('86) -> $23B ('00)",
             note="The OS toll booth -- captured the industry's economics with ~0 capital intensity.",
             sub=["What the toll booth was: MSFT wrote the operating system -- the base layer of software every PC needs to start up and run programs. It licensed DOS (then Windows) to every PC maker per unit shipped, so it collected a fee on ~every PC sold on Earth regardless of which hardware brand won the box war.",
                  "The lock-in loop it created: developers wrote apps for Windows because that is where the users were; users had to buy Windows because that is where the apps were. And each additional copy cost ~$0 to produce -- so industry unit growth converted almost directly into MSFT gross profit."]),
        dict(t="INTC", sym="INTC", n="Intel", mcap="'81 ~$1.3B -> '00 ~$500B",
             desc="x86 microprocessors (the CPU in ~every PC)",
             seg="CPUs ~25% of rev ('81, rest memory) -> ~80%+ ('00)",
             note="The other half of Wintel; 'Intel Inside' turned a component into a brand with monopoly margins.",
             sub=["The Wintel partnership: Windows was written to run only on Intel's x86 chip architecture, and Intel designed each new chip generation around what the next Windows release would need. Every Windows upgrade demanded a faster CPU; every faster CPU enabled a heavier Windows -- a mutual upgrade treadmill. Together they set the PC standard, locked out rival CPU/OS pairings, and split ~all of the industry's profit between them while the box makers fought over scraps."]),
        dict(t="CSCO", sym="CSCO", n="Cisco", mcap="'90 IPO ~$0.2B -> '00 ~$555B",
             desc="Routers and switches -- the plumbing that connected PCs into networks",
             seg="networking ~100% of rev; $70M ('90) -> $19B ('00)",
             note="PCs needed networks; the picks-and-shovels of client/server -- 1,000x from '90 IPO to '00 peak."),
        dict(t="ORCL", sym="ORCL", n="Oracle", mcap="'86 IPO ~$0.3B -> '00 ~$230B",
             desc="Relational database software for client/server systems",
             seg="database licenses/support ~90%+ of rev; $55M ('86) -> $10B ('00)",
             note="Client/server database standard; software attach to the hardware boom."),
        dict(t="HPQ", sym="HPQ", n="Hewlett-Packard", mcap="'81 ~$5B -> '00 ~$150B",
             desc="Instruments -> PCs + printers (and the ink annuity)",
             seg="computing/printing ~15% of rev ('81) -> ~80% ('00)",
             note="Rode PCs + the printer ink annuity."),
        dict(t="DELL", sym=None, nar=True, n="Dell", mcap="'88 IPO ~$0.09B -> '00 ~$130B",
             desc="Build-to-order PCs sold direct (phone, then web) -- no retail middleman",
             seg="PCs ~100% of rev; $159M ('88) -> $25B ('00)",
             note="Direct model + negative working capital = the era's best business model; roughly +90,000% from the '88 IPO to 2000. (Original listing history lost to the 2013 LBO.)",
             sub=["Negative working capital, spelled out: the customer paid Dell at the moment of ordering (day 0); Dell then built the machine from parts it paid suppliers for on ~30-60 day terms, holding only days of inventory. Cash came IN before costs went OUT -- so growth generated cash instead of consuming it. The faster Dell grew, the more free cash it threw off, while competitors had to borrow to fund inventory sitting in stores."]),
      ],
      losers=[
        dict(t="IBM", sym="IBM", n="IBM", mcap="'81 ~$34B -> '00 ~$200B (trough '93 ~$24B)",
             desc="Mainframes + services; invented the PC but outsourced its soul (OS to MSFT, CPU to INTC)",
             seg="high-margin mainframe rents ~60% of profit ('81) -> collapsing by '93; PCs never >~12% of rev",
             note="Created the PC, gave away the economics (MSFT/INTC); earnings collapsed 1991-93 -- the canonical value-trap decade."),
        dict(t="AAPL", sym="AAPL", n="Apple (in this era)", mcap="'81 ~$2B -> '00 ~$5B",
             desc="Integrated Macintosh: own hardware + own OS, sold as one product",
             seg="Mac ~100% of rev; US PC share ~16% ('81) -> ~3% ('97)",
             note="Closed model lost to Wintel; 90 days from bankruptcy in 1997 -- proof that era losers can seed the next era.",
             sub=["What 'closed model' means: Apple built BOTH the hardware and the operating system and refused to license the OS to other manufacturers -- so one company's factories and R&D competed against an entire industry of clone makers driving Wintel costs down.",
                  "Why closed lost in PCs but won in mobile: PCs were bought by corporate IT departments on price and compatibility -- an open standard licensed to everyone spreads faster and gets cheaper every year. Phones flipped the rules: they are personal, battery- and size-constrained devices where controlling hardware AND software together produces a visibly better product (speed, battery, polish), carriers subsidized the premium price, and this time Apple put its own toll booth on top (the App Store's 30% cut) -- closed integration plus platform economics instead of closed integration alone."]),
        dict(t="UIS", sym="UIS", n="Unisys", mcap="'86 merger ~$7B -> '00 ~$4B",
             desc="Burroughs + Sperry merged mainframe installed base",
             seg="legacy mainframe/services ~80% of rev -- managed decline",
             note="The merged mainframe also-rans; two melting ice cubes make a bigger ice cube."),
        dict(t="DEC", sym=None, nar=True, n="Digital Equipment", mcap="peak '87 ~$26B -> sold '98 $9.6B",
             desc="Minicomputers (VAX) -- last era's disruptor",
             seg="minis ~85% of rev; PCs ~0% -- positioned against the wave",
             note="Last era's growth star: 'no reason anyone would want a computer in their home' (Olsen, '77); peak $ in '87, sold to Compaq '98. Winners of cycle N are the shorts of cycle N+1."),
        dict(t="CPQ", sym=None, nar=True, n="Compaq", mcap="peak '99 ~$70B -> sold '02 ~$25B",
             desc="IBM-compatible PCs, retail channel",
             seg="PCs ~100% both ends -- the segment grew, the margins left (GM ~40% '87 -> ~20% late 90s)",
             note="Early PC winner (fastest to $1B in US history) -- commoditized by Dell's direct model; margin structure died before the stock; absorbed by HP (2002)."),
        dict(t="CBM", sym=None, nar=True, n="Commodore", mcap="peak '83 ~$1B -> $0 ('94)",
             desc="Cheap home computers (C64, Amiga)",
             seg="home computers ~100% of rev -- unit king, profit pauper",
             note="Outsold everyone in units (C64) at the low end -- no ecosystem, no margins; bankrupt 1994. Unit share without profit share is a trap."),
      ],
      bullets=[
      "Inflection: buy signal was the 1981 IBM PC legitimizing the category + the clone/Wintel standard (1984-86) -- standards, not boxes, carried the economics; the OS and the CPU took ~all industry profit within a decade.",
      "Sell at the peak: box makers peaked when growth shifted from 'who wins share' to 'category price deflation' (mid-90s: sub-$1,000 PCs); the sell tell was gross margin structure, visible quarters before EPS -- Compaq's 1991 margin crash previewed everyone's fate.",
      "Short/cover: IBM was the great slow short of 1987-93 (fat, high-multiple incumbent + collapsing franchise) -- but cover on regime change: Gerstner 1993 (new CEO + dividend cut + services pivot) marked the exact turn. Manage structural shorts around catalysts, not valuation.",
      "LESSON OF THE ERA: zero-marginal-cost distribution. Software replicates for free, so whoever owns the standard everyone must pass through (the OS, the CPU instruction set, the database) converts the industry's unit growth into ~pure margin -- while the companies assembling the physical boxes compete each other to zero. Own the layer, not the object."]),

 dict(id="mobile", name="Mobile / Smartphone Era", period="2005-2016", index=("^IXIC", "Nasdaq Composite"),
      start="2005-01-01", end="2017-01-01",
      winners=[
        dict(t="AAPL", sym="AAPL", n="Apple", mcap="'05 ~$30B -> '16 ~$620B",
             desc="iPhone: integrated handset + iOS + App Store toll booth",
             seg="iPhone 0% of rev ('06) -> ~63% ('16)",
             note="Redefined the category (2007) and took >80% of industry profit by 2012."),
        dict(t="QCOM", sym="QCOM", n="Qualcomm", mcap="'05 ~$70B -> '16 ~$95B",
             desc="Modem chips + patent royalties on ~every 3G/4G phone sold",
             seg="mobile ~100% of rev throughout; licensing ~30% of rev at ~85% margin",
             note="The royalty toll booth -- licensed every smartphone regardless of who won."),
        dict(t="AVGO", sym="AVGO", n="Broadcom (Avago)", mcap="'09 IPO ~$4B -> '16 ~$70B",
             desc="RF filters/amplifiers + connectivity silicon, rolled up via M&A",
             seg="wireless ~25% of rev ('09) -> ~40% ('16)",
             note="RF content per phone compounding + serial consolidation."),
        dict(t="SWKS", sym="SWKS", n="Skyworks", mcap="'05 ~$1B -> '16 ~$14B",
             desc="RF front-end modules (the radio parts of the phone)",
             seg="mobile RF ~60% of rev ('05) -> ~85% ('16); Apple ~40% of rev",
             note="Pure-play RF content story: more bands = more $ content every generation."),
        dict(t="TSM", sym="TSM", n="TSMC", mcap="'05 ~$45B -> '16 ~$160B",
             desc="Contract chip manufacturing for every SoC designer",
             seg="communications chips ~40% of rev ('05) -> ~60% ('16)",
             note="Every mobile SoC needed leading-edge foundry; the neutral arms dealer."),
        dict(t="SSNLF", sym="005930.KS", n="Samsung Electronics", mcap="'05 ~$80B -> '16 ~$220B",
             desc="Integrated: handsets + memory + displays + chip fabs",
             seg="handsets ~25% of rev ('05) -> ~45% ('13 peak), components hedging the rest",
             note="Only integrated player to win -- components (memory/AP/display) hedged the handset fight. (Local ccy.)"),
      ],
      losers=[
        dict(t="NOK", sym="NOK", n="Nokia", mcap="peak '07 ~$150B -> '16 ~$27B",
             desc="Feature-phone king running the Symbian OS",
             seg="handsets ~60% of rev ('07) -> 0 ('14, sold to MSFT); networks ~90% ('16)",
             note="40% global share in 2007 -> exited handsets 2013; software (Symbian) was the kill shot, not hardware."),
        dict(t="BB", sym="BB", n="BlackBerry", mcap="peak '08 ~$83B -> '16 ~$4B",
             desc="Enterprise email phones (keyboards, BBM, IT-department security)",
             seg="handsets ~80% of rev -> exited hardware ('16); software pivot",
             note="Enterprise lock-in was no moat vs. a better consumer product; peak $83B cap (2008) -> sub-$5B."),
        dict(t="MSI", sym="MSI", n="Motorola", mcap="'06 peak ~$55B -> handsets spun '11",
             desc="RAZR-era handsets + public-safety radios",
             seg="handsets ~40% of rev ('06) -> 0 (spun '11; Google bought it mostly for patents)",
             note="RAZR one-hit-wonder; handset unit spun and sold to Google mostly for patents."),
        dict(t="GRMN", sym="GRMN", n="Garmin", mcap="peak '07 ~$25B -> '16 ~$9B",
             desc="GPS navigation devices for cars",
             seg="auto PNDs ~75% of rev ('07) -> ~15% ('16); survived on fitness/aviation",
             note="The adjacency kill: the smartphone absorbed the PND category whole. -70% 2007-09."),
        dict(t="HTC", sym="2498.TW", n="HTC", mcap="peak '11 ~$34B -> '16 ~$2B",
             desc="Contract handset maker -> own-brand Android phones",
             seg="smartphones ~100% of rev -- no silicon, no ecosystem, nothing proprietary",
             note="First Android flagship maker; no silicon, no ecosystem, no brand moat -- peaked 2011, -95% after. (Local ccy.)"),
        dict(t="ERIC", sym="ERIC", n="Ericsson", mcap="'05 ~$50B -> '16 ~$22B",
             desc="Telecom network equipment (+ Sony handset JV)",
             seg="handsets ~25% of rev -> 0 (JV exited); networks commoditized by Huawei",
             note="Handset exit (Sony JV) + infrastructure commoditization by Huawei; the era's growth went around it."),
      ],
      bullets=[
      "Inflection: iPhone (2007) + App Store (2008) turned phones into computing platforms -- buy signal was attach economics: content-per-device (RF, foundry wafers, royalties) growing faster than units. The suppliers (QCOM, AVGO, SWKS, TSM) were buyable with less product risk than the handset fight itself.",
      "Sell at the peak: unit growth peaked ~2015 (smartphone penetration saturated) -- sell tell for the content names was deceleration in $-content growth + customer concentration risk repricing (SWKS/QCOM 2015-16 when Apple units flattened); in platform eras, sell the component names when the device S-curve flattens, before the ecosystem names.",
      "Short/cover: incumbent handset shorts (NOK, BB) worked on the software/ecosystem gap, and the cover signal was capitulation-exit events (Nokia selling to MSFT 2013, BB going enterprise-software) -- by then the equity had already lost 90%+; the money was made in years 1-3 of denial, when 'cheap' and 'installed base' were the bull case.",
      "LESSON OF THE ERA: content-per-device beats device share. The durable money was dollars of content on EVERY unit sold regardless of which brand won -- QCOM's royalty, AVGO/SWKS's RF chips, TSMC's wafers. If you must own a device maker, own the one with a software toll booth on top of the hardware (Apple); hardware share without an ecosystem is a melting asset (Nokia, HTC)."]),

 dict(id="cloud", name="Cloud Era", period="2010-2021", index=("^IXIC", "Nasdaq Composite"),
      start="2010-01-01", end="2022-01-01",
      winners=[
        dict(t="AMZN", sym="AMZN", n="Amazon (AWS)", mcap="'10 ~$60B -> '21 ~$1.7T",
             desc="E-commerce + AWS: renting compute/storage by the hour",
             seg="AWS 0% of rev ('10) -> ~13% of rev but ~75% of operating profit ('21)",
             note="Invented the category; retail cash funded a software-margin monopoly nobody modeled until 2015 disclosure."),
        dict(t="MSFT", sym="MSFT", n="Microsoft", mcap="'10 ~$220B -> '21 ~$2.5T",
             desc="Windows/Office incumbent converted to Azure + subscriptions",
             seg="cloud ~5% of rev ('11) -> ~45%+ ('21)",
             note="The great incumbent transition: Nadella (2014) pivoted the installed base to Azure/SaaS -- multiple went 10x->35x."),
        dict(t="CRM", sym="CRM", n="Salesforce", mcap="'10 ~$12B -> '21 ~$250B",
             desc="Sales software rented by the seat -- the original SaaS template",
             seg="subscription ~95% of rev throughout; $1.3B ('10) -> $26B ('21)",
             note="Proved the SaaS model at scale; the template every software company re-rated on."),
        dict(t="NOW", sym="NOW", n="ServiceNow", mcap="'12 IPO ~$3B -> '21 ~$130B",
             desc="IT-workflow software as a subscription",
             seg="subscription ~95% of rev; $93M ('12) -> $5.9B ('21)",
             note="Pure-play SaaS compounder -- 20%+ growth for a decade straight."),
        dict(t="ADBE", sym="ADBE", n="Adobe", mcap="'10 ~$17B -> '21 ~$270B",
             desc="Creative software: shrink-wrapped licenses -> Creative Cloud subscription",
             seg="subscription ~5% of rev ('11) -> ~92% ('21)",
             note="The license->subscription conversion playbook: revenue dipped, LTV soared, stock 10x'd."),
        dict(t="NVDA", sym="NVDA", n="NVIDIA", mcap="'10 ~$9B -> '21 ~$735B",
             desc="GPUs: gaming graphics -> the datacenter's ML compute engine",
             seg="datacenter ~5% of rev ('12) -> ~40% ('21)",
             note="GPUs became the cloud's compute engine (ML) -- the cloud era's semis winner and the bridge to the AI era."),
      ],
      losers=[
        dict(t="IBM", sym="IBM", n="IBM", mcap="'10 ~$180B -> '21 ~$120B",
             desc="Legacy services, middleware and mainframes, relabeled 'cloud'",
             seg="genuine public cloud <10% of rev; legacy ~60%+ all decade",
             note="'Cloud-washed' legacy services for a decade; revenue declined 2012-2020 while buying back stock -- financial engineering vs. secular decline loses."),
        dict(t="ORCL", sym="ORCL", n="Oracle (2010s)", mcap="'10 ~$130B -> '21 ~$240B",
             desc="On-prem database licenses defended, cloud denied",
             seg="cloud ~2% of rev ('12) -> ~25% ('21) -- a decade late, then it worked",
             note="Denied cloud ('gibberish' -- Ellison 2008), lost a decade of relative performance defending license margins."),
        dict(t="TDC", sym="TDC", n="Teradata", mcap="peak '12 ~$13B -> '21 ~$4B",
             desc="On-prem data-warehouse appliances",
             seg="on-prem EDW ~90% of rev -- exactly the workload Snowflake/Redshift ate",
             note="On-prem data warehouse -- the exact workload Snowflake/Redshift ate. -75% from 2012 peak."),
        dict(t="HPE", sym="HPE", n="HP Enterprise", mcap="'15 spin ~$27B -> '21 ~$21B",
             desc="Servers/storage/networking for corporate datacenters",
             seg="on-prem hardware ~85% of rev -- the workloads moved to clouds that self-build",
             note="Selling servers to companies that were moving compute to clouds that build their own."),
        dict(t="DXC", sym="DXC", n="DXC Technology", mcap="'17 ~$20B -> '21 ~$8B",
             desc="Legacy IT-outsourcing rollup (HPE services + CSC)",
             seg="traditional outsourcing ~100% of rev; shrinking pie + leverage",
             note="Legacy IT outsourcing rollup -- shrinking pie, leverage, serial restructuring."),
        dict(t="NTAP", sym="NTAP", n="NetApp", mcap="'10 ~$20B -> '21 ~$20B",
             desc="On-prem storage appliances ('filers') for enterprise datacenters",
             seg="on-prem ~95% of rev ('10) -> ~90% ('21); cloud services <5%",
             note="On-prem storage: survived but ceded the growth; a decade of flat revenue in a 30%-CAGR category.",
             sub=["Why it stalled even though enterprises kept buying storage: the INCREMENTAL data -- the growth -- went to hyperscalers, and hyperscalers don't buy branded storage appliances; they build from commodity drives plus their own software. Meanwhile AWS S3 turned storage into a per-GB-per-month utility, crushing the appliance pricing umbrella. NetApp kept its on-prem installed base (hence flat revenue, not collapse), but markets pay multiples for growth, and all the growth happened in datacenters NetApp couldn't sell into. Flat in a 30%-CAGR category IS losing."]),
      ],
      bullets=[
      "THE LAYERS -- same word, two different businesses: 'cloud' was two shifts stacked on top of each other. INFRASTRUCTURE (IaaS: AWS, Azure, GCP) = renting raw compute/storage/networking by the hour -- capex-heavy, usage-metered, decent-but-hardware margins, and the ONLY layer that buys silicon at scale. APPLICATIONS (SaaS: CRM, NOW, ADBE) = finished software rented by the seat -- ~80% gross margin, almost no capex, contracted recurring revenue, and it RUNS ON the IaaS layer rather than building datacenters. For semis: SaaS growth is a demand signal, but IaaS capex is where the silicon dollars actually land -- hyperscaler capex converts nearly dollar-for-dollar into servers, GPUs, memory, optics and power gear.",
      "PRE-HISTORY -- how software got to 'cloud' in three models: (1) CUSTOM era, 1950s-60s: all software was bespoke -- written in-house or bundled free with the mainframe, because every machine was different and there was no way to distribute programs at scale. (2) PRE-PACKAGED era, 1970s-90s: IBM's 1969 unbundling (pricing software separately from hardware, under antitrust pressure) created a market for software as a PRODUCT -- SAP (1972), Oracle (1977), then shrink-wrapped PC software (MSFT, Lotus): perpetual license upfront + ~20%/yr maintenance, run on YOUR servers, upgraded every few years as a painful project. Packaging happened because custom was slow, expensive and duplicated -- write once, sell 10,000x is the better business. (3) SaaS era, ~2000-: Salesforce sold the same category of software as a hosted subscription -- vendor runs it, always current, opex not capex. Each transition moved the profit pool: hardware -> licenses -> subscriptions.",
      "WHY THE ERA DATES FROM ~2010 (not 2006, when AWS launched EC2): eras start when the COST CURVE crosses, not when the technology ships. By 2010-12 the pieces aligned -- post-GFC budgets favored opex over capex, virtualization was mature, AWS had scale-proven reliability and years of price cuts, smartphones/consumer internet forced companies onto infrastructure that could handle spiky demand, and the 2012 SaaS IPO class (NOW, WDAY) gave public markets pure-plays to price the model. Before ~2010 cloud was an experiment; after, it was the default for new workloads.",
      "Inflection: buy signal was unit economics disclosure -- AWS's first segment print (Apr-2015: 17% margin, 50% growth) repriced the whole complex; before that the tell was capex: hyperscaler capex inflected 2013-15 while enterprise IT spend stalled. Follow the capex, it IS the cycle (same signal this dashboard tracks).",
      "Sell at the peak: the era's blowoff was 2020-21 -- sell tell was valuation regime dependence: SaaS at 30-40x SALES only works at 0% rates; when the rate regime turned (2021), the highest-multiple cohort fell 70-80% regardless of execution. Sell the multiple, not the company.",
      "Short/cover: legacy IT shorts (IBM, TDC, DXC) were grinding structural donors -- cover on genuine business-model regime change only (IBM: Kyndryl spin + AI narrative 2023 re-rated it; ORCL: OCI/AI capex turned it 2023) -- 'new CEO + real product cycle' is the cover signal, dividend yield is not.",
      "LESSON OF THE ERA: recurring revenue re-rates, boxes don't. Renting software/compute monthly (opex) beat selling boxes (capex) for the customer, and for the vendor it converted one-time sales into compounding annuities the market pays 10x revenue for. The moat behind it was capex-at-scale: only players pouring $10B+/yr into datacenters -- or converting a giant installed base to subscription (MSFT, ADBE) -- kept the economics. Follow the capex; it IS the cycle."]),

 dict(id="covid", name="COVID Boom & Bust", period="2019-2023", index=("^IXIC", "Nasdaq Composite"),
      start="2019-01-01", end="2024-01-01",
      winners=[
        dict(t="NVDA", sym="NVDA", n="NVIDIA", mcap="'19 ~$85B -> '23 ~$1.2T",
             desc="GPUs: gaming + datacenter -> AI compute",
             seg="datacenter ~30% of rev ('19) -> ~56% ('23)",
             note="Gaming/datacenter pull-forward, -66% in 2022 inventory bust, then the AI supercycle -- the full cycle in one chart."),
        dict(t="AAPL", sym="AAPL", n="Apple", mcap="'19 ~$700B -> '23 ~$3.0T",
             desc="iPhone + growing services attach (App Store, subscriptions)",
             seg="services ~18% of rev ('19) -> ~22% ('23)",
             note="Stay-at-home device demand + services; the quality compounder path through the whole event."),
        dict(t="MSFT", sym="MSFT", n="Microsoft", mcap="'19 ~$780B -> '23 ~$2.8T",
             desc="Azure/O365/Teams -- the enterprise digitization checkbook",
             seg="cloud ~33% of rev ('19) -> ~55% ('23)",
             note="Teams/Azure -- the enterprise digitization checkbook."),
        dict(t="AMD", sym="AMD", n="AMD", mcap="'19 ~$20B -> '23 ~$240B",
             desc="CPUs/GPUs riding server share gains vs Intel",
             seg="datacenter ~10% of rev ('19) -> ~30% ('23)",
             note="PC/console/server demand surge + share gains vs Intel; held most of the re-rate."),
        dict(t="TSLA", sym="TSLA", n="Tesla", mcap="'19 ~$60B -> '23 ~$790B (peak '21 ~$1.2T)",
             desc="EVs reaching manufacturing scale",
             seg="deliveries 367K ('19) -> 1.81M ('23)",
             note="The liquidity era's defining momentum asset -- 15x in 18 months; also the regime-change casualty (-73% in 2022).") ,
        dict(t="SHOP", sym="SHOP", n="Shopify", mcap="'19 ~$15B -> '23 ~$100B (peak ~$210B)",
             desc="E-commerce infrastructure for independent merchants",
             seg="GMV $61B ('19) -> $236B ('23)",
             note="E-commerce pull-forward poster child: 10x up, -85% down, then a real business re-emerged -- separates COMPANY from PULL-FORWARD."),
      ],
      losers=[
        dict(t="ZM", sym="ZM", n="Zoom", mcap="peak '20 ~$160B -> '23 ~$18B",
             desc="Video meetings",
             seg="video ~100% of rev; usage 10M ('19) -> 300M daily participants ('20), SMB churned back",
             note="Peak cap > ExxonMobil on a feature; TAM pull-forward priced as TAM expansion. -90%."),
        dict(t="PTON", sym="PTON", n="Peloton", mcap="peak '21 ~$50B -> '23 ~$2B",
             desc="Connected exercise bikes + content subscription",
             seg="hardware ~80% of rev at peak; subs 700K ('19) -> 3M ('22), then churn + inventory glut",
             note="Hardware demand spike modeled as a subscription annuity; inventory + churn killed it. -98%."),
        dict(t="DOCU", sym="DOCU", n="DocuSign", mcap="peak '21 ~$56B -> '23 ~$12B",
             desc="E-signature software",
             seg="e-sign ~95% of rev -- a one-time adoption step, not a compounding curve",
             note="Real product, one-time adoption step-function priced as permanent growth. -85%."),
        dict(t="TDOC", sym="TDOC", n="Teladoc", mcap="peak '21 ~$44B -> '23 ~$3.5B",
             desc="Telehealth visits + chronic-care (Livongo)",
             seg="visits 4M ('19) -> 15M ('20); bought Livongo for $18.5B at the top, wrote most of it off",
             note="Peak-cycle M&A (Livongo, $18.5B) at the top -- goodwill writedowns did the accounting confession later."),
        dict(t="ROKU", sym="ROKU", n="Roku", mcap="peak '21 ~$60B -> '23 ~$13B",
             desc="TV streaming platform monetized by ads",
             seg="platform/ads ~55% of rev ('19) -> ~85% ('23) -- right mix shift, wrong ad cycle",
             note="Streaming hours pulled forward + ad market turned; -90% from peak."),
        dict(t="NFLX", sym="NFLX", n="Netflix (2021-22)", mcap="'19 ~$150B -> '23 ~$210B (trough '22 ~$80B)",
             desc="Streaming video subscriptions",
             seg="subs 167M ('19) -> 231M ('23); the Apr-22 print (-1M subs) broke the narrative",
             note="The subscriber miss (Apr-22) that repriced the whole 'growth at any price' complex in one print; -75% peak-to-trough, then recovered on the ads/paid-sharing model turn."),
      ],
      bullets=[
      "Inflection: the buy was policy + behavior change (Mar-Apr 2020): unlimited QE plus a forced digitization experiment -- the tell for sizing up was fiscal transfers hitting consumer accounts while the entire sell side modeled a demand collapse.",
      "Sell at the peak: distinguish pull-forward from TAM change -- the sell tell was decelerating cohort/usage data against accelerating consensus (ZM churn, PTON engagement, 2H-21) plus the speculative tape breaking first (ARKK/SPACs peaked Feb-21, 10 months before the index). When the beneficiaries start buying growth at the top (TDOC/Livongo), the organic story is over.",
      "Short/cover: COVID-darling shorts paid for 18 months straight -- cover tell was the accounting confession cycle completing (writedowns, guidance kitchen-sinks, mgmt turnover: PTON new CEO Feb-22, kitchen-sink guides through 2022) and real FCF appearing at the survivors (NFLX ads pivot). Bust survivors with a second act (SHOP, NFLX) became the next longs -- same as AMZN 2002.",
      "LESSON OF THE ERA: pull-forward is not TAM change. A demand shock spends FUTURE demand today, but the market priced it as a new, permanently steeper S-curve. Underwrite the cohort and usage data, not the narrative -- and when the beneficiaries start ACQUIRING growth at peak prices (Teladoc/Livongo), the organic curve has already bent."]),
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
    out = {k: cfg[k] for k in ("t", "n", "note", "mcap", "desc", "seg", "sub") if k in cfg}
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
