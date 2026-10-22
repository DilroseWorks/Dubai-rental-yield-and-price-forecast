"""Dubai Yield Map: rental yield, price momentum and a 12-month outlook for Dubai communities.

Run locally:   streamlit run app/streamlit_app.py
Data:          app/data/*.csv, produced by python/07_export_powerbi.py and copied by python/08_prepare_app_data.py
"""
import sys
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from calc import (MODEL_NAMES, backtest_table, count_words, data_as_of, estimate_yield,  # noqa: E402
                  load_data, mark_high_and_rising, market_kpis, scenario_series_for, scenario_values,
                  signed_pct, yield_colours)
from tile_layout import COLS, ROWS, SCATTER_LABELS, tile_for  # noqa: E402

st.set_page_config(page_title="Dubai Yield Map", page_icon=":material/grid_view:", layout="wide")

# ---------------------------------------------------------------- design tokens
INK, MUTED, BODY, LINE, PAPER = "#111418", "#50565E", "#2C3137", "#D9DCD6", "#F7F7F4"
DEEP, MID, CORAL, GREY_DOT, GRID = "#0B3C5D", "#1F6F9B", "#C2452B", "#8C949C", "#ECEDE8"
FONT = "Readex Pro"

st.html("""<style>
@import url('https://fonts.googleapis.com/css2?family=Readex+Pro:wght@300;400;500;600;700&family=Reem+Kufi:wght@500&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp li,
.stApp [data-baseweb="select"] * { font-family: 'Readex Pro', system-ui, sans-serif; }
.stApp { background: #F7F7F4; color: #111418; }
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stDecoration"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1280px; padding: 0 clamp(16px, 4vw, 48px) 32px; }
[data-testid="stHtml"] a { color: #111418; text-decoration: none; }
[data-testid="stHtml"] a:hover { color: #C2452B; }

/* Top bar: fixed, so the section links stay on screen while scrolling */
.dym-topbar { position: fixed; top: 0; left: 0; right: 0; z-index: 999990;
  background: rgba(247, 247, 244, 0.96); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid #D9DCD6; }
.dym-topbar-inner { max-width: 1280px; margin: 0 auto; padding: 0 clamp(16px, 4vw, 48px); height: 68px;
  display: flex; justify-content: space-between; align-items: center; gap: 24px; }
.dym-nav { display: flex; gap: 28px; font-size: 15px; white-space: nowrap; }
.dym-nav a { padding: 12px 0; border-bottom: 2px solid transparent; }
.dym-nav a:hover { border-bottom-color: #C2452B; }
.dym-topbar-space { height: 68px; }
.dym-short { display: none; }
#top, #map, #invest, #outlook, #calc, #method { scroll-margin-top: 84px; }
html, [data-testid="stMain"] { scroll-behavior: smooth; }
@media (max-width: 760px) {
  .dym-topbar-inner { height: auto; flex-direction: column; align-items: stretch; gap: 0; padding-top: 10px; }
  .dym-nav { gap: 18px; overflow-x: auto; font-size: 14px; scrollbar-width: none; }
  .dym-long { display: none; } .dym-short { display: inline; }
  .dym-method-table { min-width: 0 !important; font-size: 13px !important; }
  .dym-method-table th, .dym-method-table td { padding-left: 6px !important; padding-right: 6px !important; }
  .dym-topbar-space { height: 100px; }
  #top, #map, #invest, #outlook, #calc, #method { scroll-margin-top: 112px; }
}

/* Hide Streamlit's chart toolbar (download / fullscreen icons) */
[data-testid="stElementToolbar"] { display: none !important; }

/* Flats / Villas switch */
[data-testid="stButtonGroup"] [role="radiogroup"] { gap: 0; }
button[data-variant="segmented_control"] {
  min-height: 44px; padding: 0 24px; border-radius: 0; border: 1px solid #111418; margin: 0 0 0 -1px;
  background: #FFFFFF; color: #111418; font-weight: 500; }
button[data-variant="segmented_control"] p { color: #111418; font-weight: 500; }
button[data-variant="segmented_control"][aria-checked="true"] { background: #111418 !important; border-color: #111418 !important; }
button[data-variant="segmented_control"][aria-checked="true"] p { color: #F7F7F4 !important; }

/* White cards (scatter, outlook) */
.st-key-scatter_card, .st-key-outlook_card {
  background: #FFFFFF; border: 1px solid #D9DCD6; border-radius: 0; padding: clamp(16px, 2.5vw, 32px); }
.st-key-outlook_card, .st-key-calc_card { height: 100%; }
[data-testid="stLayoutWrapper"]:has(> .st-key-calc_card), [data-testid="stLayoutWrapper"]:has(> .st-key-outlook_card) { flex: 1 1 auto; }
.st-key-scatter_card { overflow-x: auto; }
.st-key-scatter_card [data-testid="stVegaLiteChart"] { min-width: 760px; }
.phone-only { display: none; }
@media (max-width: 700px) { .phone-only { display: block; } }
.st-key-outlook_card .stSelectbox [role="group"] { background: #F7F7F4; border-color: #D9DCD6; border-radius: 0; }

/* Dark calculator panel */
.st-key-calc_card { background: #111418; color: #F7F7F4; padding: clamp(20px, 3vw, 36px); }
.st-key-calc_card [data-testid="stWidgetLabel"] p { color: #A9AFB6; font-size: 13px; }
.st-key-calc_card .stSelectbox [role="group"],
.st-key-calc_card [data-testid="stNumberInputContainer"] { background: #1C2026; border: 1px solid #3A4048; border-radius: 0; }
.st-key-calc_card .stSelectbox input, .st-key-calc_card [data-testid="stNumberInputField"] {
  background: #1C2026; color: #F7F7F4; -webkit-text-fill-color: #F7F7F4; }
.st-key-calc_card .stSelectbox button, .st-key-calc_card [data-testid="stNumberInputContainer"] button {
  background: #1C2026; color: #A9AFB6; }
.st-key-calc_card [data-testid="stExpander"] details { border: 1px solid #3A4048; border-radius: 0; background: transparent; }
.st-key-calc_card [data-testid="stExpander"] summary, .st-key-calc_card [data-testid="stExpander"] summary p,
.st-key-calc_card [data-testid="stExpander"] summary span { color: #D4D8DC; }
.st-key-calc_card button[data-variant="segmented_control"] { background: transparent; border-color: #3A4048; }
.st-key-calc_card button[data-variant="segmented_control"] p { color: #F7F7F4; }
.st-key-calc_card button[data-variant="segmented_control"][aria-checked="true"] { background: #E6EEF2 !important; border-color: #E6EEF2 !important; }
.st-key-calc_card button[data-variant="segmented_control"][aria-checked="true"] p { color: #0B1B26 !important; }
</style>""")


# ---------------------------------------------------------------- data
@st.cache_data
def get_data():
    return load_data()


try:
    D = get_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

score = D["community_scorecard"]
as_of = data_as_of(D["index_lines"])
K = market_kpis(D)
SEGMENTS = {"Flats": "Flat", "Villas": "Villa"}


def eyebrow(text: str, color: str = DEEP) -> str:
    return (f'<div style="font-size: 13px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; '
            f'color: {color}">{text}</div>')


# Both Flats/Villas switches (map and scatter) share one setting.
if "segment" not in st.session_state:
    st.session_state.segment = "Flats"
    st.session_state.seg_map = st.session_state.seg_scatter = "Flats"


def _sync(src: str, other: str):
    st.session_state.segment = st.session_state[src]
    st.session_state[other] = st.session_state[src]


def segment_switch(key: str, other: str):
    st.segmented_control("Property type", list(SEGMENTS), key=key, required=True, label_visibility="collapsed",
                         on_change=_sync, args=(key, other))


# ---------------------------------------------------------------- header and hero
st.html(f"""
<div class="dym-topbar"><div class="dym-topbar-inner">
  <a href="#top" aria-label="Back to top" style="display: flex; align-items: center; gap: 12px">
    <div aria-hidden="true" style="position: relative; width: 32px; height: 32px; flex: none"><div style="position: absolute; left: 7px; top: 7px; width: 18px; height: 18px; background: {DEEP}"></div><div style="position: absolute; left: 7px; top: 7px; width: 18px; height: 18px; background: {DEEP}; transform: rotate(45deg)"></div><div style="position: absolute; left: 12px; top: 12px; width: 8px; height: 8px; border-radius: 50%; background: {PAPER}"></div></div>
    <div style="font-weight: 600; font-size: 18px; letter-spacing: -0.01em">Dubai Yield Map</div>
    <span lang="ar" dir="rtl" style="font-family: 'Reem Kufi', sans-serif; font-weight: 500; font-size: 18px; color: {MUTED}">خريطة العائد</span>
  </a>
  <nav aria-label="Sections" class="dym-nav">
    <a href="#map">Map</a>
    <a href="#invest"><span class="dym-long">Where to invest</span><span class="dym-short">Invest</span></a>
    <a href="#outlook">Outlook</a>
    <a href="#calc">Calculator</a>
    <a href="#method">Method</a>
  </nav>
</div></div>
<div id="top" class="dym-topbar-space"></div>
<section style="display: flex; flex-direction: column; gap: 28px; padding: clamp(36px, 5vw, 72px) 0 32px">
  <div style="display: flex; flex-direction: column; gap: 20px">
    {eyebrow("Dubai flats and villas")}
    <h1 style="margin: 0; padding: 0; font-family: '{FONT}', sans-serif; font-weight: 600; font-size: clamp(40px, 5.4vw, 80px); line-height: 1.2; letter-spacing: -0.035em; color: {INK}"><span style="display: block">The lights are on the water.</span><span style="display: block; color: {MID}">The yield is inland.</span></h1>
  </div>
  <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 20px 64px">
    <p style="margin: 0; max-width: 600px; font-size: 19px; line-height: 1.55; color: {BODY}; font-weight: 300">Each tile is a community, laid out roughly where it sits between the Gulf and the desert. Darker tiles pay a higher gross yield on Jan–{as_of:%b %Y} leases. The number underneath is the price change on the same projects over the last six months.</p>
    <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding-bottom: 4px" aria-label="Legend: gross yield">
      <div style="font-size: 13px; color: {MUTED}; margin-right: 6px">Gross yield</div>
      <div style="padding: 6px 10px; background: #E6EEF2; border: 1px solid #C9D6DE; font-size: 13px">under 5.5%</div>
      <div style="padding: 6px 10px; background: #B5D3E4; border: 1px solid #B5D3E4; font-size: 13px">5.5–6.5</div>
      <div style="padding: 6px 10px; background: #6FA8CB; border: 1px solid #6FA8CB; font-size: 13px; color: #0B1B26">6.5–7.5</div>
      <div style="padding: 6px 10px; background: #1F6F9B; border: 1px solid #1F6F9B; font-size: 13px; color: #FFFFFF">7.5–8.5</div>
      <div style="padding: 6px 10px; background: #0B3C5D; border: 1px solid #0B3C5D; font-size: 13px; color: #FFFFFF">8.5% and up</div>
    </div>
  </div>
</section>
<div id="map"></div>
""")

# ---------------------------------------------------------------- tile map
c1, c2 = st.columns([1, 3], vertical_alignment="center")
with c1:
    segment_switch("seg_map", "seg_scatter")
seg_label = st.session_state.segment
seg = SEGMENTS[seg_label]
s_seg = mark_high_and_rising(score[score["segment"] == seg])
avg_yield = s_seg["gross_yield_pct"].mean()
flat_avg = score[score["segment"] == "Flat"]["gross_yield_pct"].mean()
with c2:
    if seg == "Flat":
        note = (f"{len(s_seg)} flat communities. The waterfront pays the least; the outer communities pay the most.")
    else:
        best = s_seg["gross_yield_pct"].max()
        note = (f"{len(s_seg)} villa communities, on the same colour scale as flats. "
                + ("Even the best villa yield is below the " if best < flat_avg else "The best villa yield is above the ")
                + f"{flat_avg:.1f}% flat average.")
    st.html(f'<div style="font-size: 15px; color: {BODY}">{escape(note)}</div>')

tiles, unplaced = [], []
for r in s_seg.itertuples():
    t = tile_for(seg, r.area)
    if t is None:
        unplaced.append(r.community_name)
        continue
    col, row, label = t
    bg, fg = yield_colours(r.gross_yield_pct)
    border = "#C9D6DE" if bg == "#E6EEF2" else bg
    m = r.price_yoy_6m_pct
    arrow = ""
    if pd.notna(m) and m != 0:
        edge = "border-bottom" if m > 0 else "border-top"
        arrow = (f'<span aria-hidden="true" style="display: inline-block; width: 0; height: 0; border-left: 4.5px solid transparent; '
                 f'border-right: 4.5px solid transparent; {edge}: 8px solid {fg}"></span>')
    tip = f"{r.community_name}: gross yield {r.gross_yield_pct:.1f}%, 6-month price change {signed_pct(m)}"
    tiles.append(f"""<div title="{escape(tip)}" style="grid-column: {col + 1}; grid-row: {row + 1}; background: {bg}; color: {fg}; border: 1px solid {border}; padding: 10px 10px 9px; display: flex; flex-direction: column; justify-content: space-between; gap: 4px; position: relative; z-index: 1; min-width: 0">
<div style="font-size: 12px; font-weight: 500; line-height: 1.25">{escape(label)}</div>
<div style="font-size: 26px; font-weight: 600; line-height: 1; letter-spacing: -0.02em">{r.gross_yield_pct:.1f}%</div>
<div style="display: flex; align-items: center; gap: 4px; font-size: 12px; line-height: 1">{arrow}<span>{signed_pct(m)}</span></div>
</div>""")

coast_note = ""
if not any(tile_for(seg, a) and tile_for(seg, a)[1] == 1 for a in s_seg["area"]):
    coast_note = (f'<div style="grid-column: 1 / {COLS + 1}; grid-row: 2; border: 1px dashed #B9C2C9; display: flex; '
                  f'align-items: center; justify-content: center; padding: 0 20px; font-size: 14px; color: {MUTED}">'
                  f'No waterfront {seg.lower()} area has enough leases and sales (50 of each) to be measured.</div>')

st.html(f"""
<p class="phone-only" style="margin: 0 0 8px; font-size: 13px; color: {MUTED}">Swipe sideways to see the whole map.</p>
<section aria-label="Tile map of gross yield by community" style="overflow-x: auto; padding-bottom: 8px">
<div style="min-width: 980px">
<div style="display: grid; grid-template-columns: repeat({COLS}, minmax(0, 1fr)); grid-template-rows: repeat({ROWS}, minmax(108px, auto)); gap: 6px">
<div style="grid-column: 1 / {COLS + 1}; grid-row: 1; background: #DCE8EF; display: flex; align-items: center; padding: 0 20px">
<div style="display: flex; flex-direction: column; gap: 2px">
<div style="font-size: 13px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: #2C4A5E">Arabian Gulf</div>
<div lang="ar" dir="rtl" style="font-family: 'Reem Kufi', sans-serif; font-size: 16px; color: #2C4A5E; text-align: left">الخليج العربي</div>
</div>
</div>
{coast_note}{"".join(tiles)}
</div>
<div style="display: flex; justify-content: space-between; gap: 16px; padding-top: 12px; font-size: 13px; color: {MUTED}">
<div>West: Jebel Ali, towards Abu Dhabi</div><div>Inland: Dubailand and the desert</div><div>East: Deira, towards Sharjah</div>
</div>
</div>
</section>
<p style="margin: 8px 0 0; font-size: 13px; color: {MUTED}">Schematic, not to scale. "No data" means fewer than 3 projects had repeat sales. Gross yield is before service charges, vacancy and fees.{(" Not on the map: " + escape(", ".join(unplaced)) + ".") if unplaced else ""}</p>
""")

# ---------------------------------------------------------------- market cards
def card(value: str, text: str, color: str = INK) -> str:
    return (f'<div style="background: #FFFFFF; border: 1px solid {LINE}; padding: 24px; display: flex; flex-direction: column; gap: 8px">'
            f'<div style="font-size: 44px; font-weight: 600; line-height: 1; letter-spacing: -0.03em; color: {color}">{value}</div>'
            f'<div style="font-size: 14px; color: {MUTED}">{text}</div></div>')


st.html(f"""
<section aria-label="Market at a glance" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); gap: 12px; padding: 56px 0 0">
{card(signed_pct(K.sales_change_pct), f"Sales volume, {K.window_label} vs the same months a year earlier", CORAL if K.sales_change_pct < 0 else DEEP)}
{card(f"{K.index_latest:.1f}", "Ready flat price index, Jan 2020 = 100, same projects")}
{card(signed_pct(K.below_peak_pct), f"Below the index peak of {K.peak_month:%b %Y}", CORAL)}
{card(signed_pct(K.new_lease_premium_pct, 0), f"New flat tenants pay over renewing ones: AED {K.new_rent_per_sqm:,.0f} vs {K.renewed_rent_per_sqm:,.0f} per sqm, {K.rents_month:%b %Y}", DEEP)}
</section>
<div id="invest" style="height: 40px"></div>
""")

# ---------------------------------------------------------------- scatter
n_hot = int(s_seg["high_and_rising"].sum())
kind = "communities" if seg == "Flat" else "villa communities"
if n_hot == 1:
    scatter_title = f"One {kind[:-3]}y pays above average and is still rising"
else:
    scatter_title = f"{count_words(n_hot)} {kind} pay above average and are still rising"

h1, h2 = st.columns([3, 1], vertical_alignment="bottom")
with h1:
    st.html(f"""<div style="display: flex; flex-direction: column; gap: 12px; max-width: 920px">
{eyebrow("Where to invest")}
<h2 style="margin: 0; padding: 0; font-family: '{FONT}', sans-serif; font-weight: 600; font-size: clamp(34px, 4.2vw, 56px); line-height: 1.12; letter-spacing: -0.03em; color: {INK}">{scatter_title}</h2>
</div>""")
with h2:
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="medium"):
        st.html(f'<div style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: {BODY}; white-space: nowrap">'
                f'<span aria-hidden="true" style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: {DEEP}"></span>'
                f'High yield, prices rising</div>', width="content")
        segment_switch("seg_scatter", "seg_map")

measured = s_seg.dropna(subset=["price_yoy_6m_pct"]).copy()
labels = SCATTER_LABELS.get(seg, {})
measured["label_pos"] = measured["area"].map(labels).fillna("")
measured["label"] = measured.apply(
    lambda r: (f"{tile_for(seg, r['area'])[2] if tile_for(seg, r['area']) else r['community_name']}"
               + (f" {r['gross_yield_pct']:.1f}%" if r["high_and_rising"] and r["gross_yield_pct"] >= measured["gross_yield_pct"].nlargest(2).min() else "")
               + (" (few projects)" if r["projects_6m"] < 5 and r["label_pos"] else "")), axis=1)
measured["change"] = measured["price_yoy_6m_pct"].map(signed_pct)
measured["yield_txt"] = measured["gross_yield_pct"].map("{:.1f}%".format)

xmin = min(-5.0, (measured["price_yoy_6m_pct"].min() - 2) // 5 * 5)
xmax = max(5.0, -((-(measured["price_yoy_6m_pct"].max() + 2)) // 5) * 5)
ymin = (measured["gross_yield_pct"].min() - 0.3) * 2 // 1 / 2
ymax = -((-(measured["gross_yield_pct"].max() + 0.3) * 2) // 1) / 2

base = alt.Chart(measured)
x_ticks = list(range(int(xmin), int(xmax) + 1, 5))
y_ticks = [v / 2 for v in range(int(ymin * 2), int(ymax * 2) + 1)] if ymax - ymin <= 3 else list(range(int(ymin), int(ymax) + 1))
SX = alt.Scale(domain=[xmin, xmax], nice=False, zero=False)
SY = alt.Scale(domain=[ymin, ymax], nice=False, zero=False)
x_enc = alt.X("price_yoy_6m_pct:Q", title="Price change, last 6 months vs a year earlier, same projects", scale=SX,
              axis=alt.Axis(values=x_ticks, labelExpr="(datum.value > 0 ? '+' : '') + datum.value + '%'"))
y_enc = alt.Y("gross_yield_pct:Q", title="Gross yield", scale=SY,
              axis=alt.Axis(values=y_ticks, labelExpr="datum.value + '%'"))
quad = alt.Chart(pd.DataFrame({"x": [0], "x2": [xmax], "y": [avg_yield], "y2": [ymax]})).mark_rect(
    color=DEEP, opacity=0.05, tooltip=False).encode(x=alt.X("x:Q", scale=SX), x2="x2:Q", y=alt.Y("y:Q", scale=SY), y2="y2:Q")
vline = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=GREY_DOT, strokeDash=[4, 4], tooltip=False).encode(x=alt.X("x:Q", scale=SX))
hline = alt.Chart(pd.DataFrame({"y": [avg_yield]})).mark_rule(color=GREY_DOT, strokeDash=[4, 4], tooltip=False).encode(y=alt.Y("y:Q", scale=SY))
corner = alt.Chart(pd.DataFrame({"x": [xmax], "y": [ymax], "t": ["HIGH YIELD · RISING"]})).mark_text(
    align="right", baseline="top", dx=-8, dy=8, fontSize=13, fontWeight=600, color=DEEP, tooltip=False).encode(
    x=alt.X("x:Q", scale=SX), y=alt.Y("y:Q", scale=SY), text="t:N")
corner2 = alt.Chart(pd.DataFrame({"x": [xmin], "y": [ymin], "t": ["LOW YIELD · FALLING"]})).mark_text(
    align="left", baseline="bottom", dx=8, dy=-8, fontSize=13, fontWeight=600, color=CORAL, tooltip=False).encode(
    x=alt.X("x:Q", scale=SX), y=alt.Y("y:Q", scale=SY), text="t:N")
avg_txt = alt.Chart(pd.DataFrame({"x": [xmax], "y": [avg_yield], "t": [f"average {avg_yield:.1f}%"]})).mark_text(
    align="right", baseline="bottom", dx=-4, dy=-4, fontSize=12, color=MUTED, tooltip=False).encode(x=alt.X("x:Q", scale=SX), y=alt.Y("y:Q", scale=SY), text="t:N")
tooltip = [alt.Tooltip("community_name:N", title="Community"), alt.Tooltip("yield_txt:N", title="Gross yield"),
           alt.Tooltip("change:N", title="6-month price change"), alt.Tooltip("projects_6m:Q", title="Projects measured")]
points = base.mark_circle(opacity=1).encode(
    x=x_enc, y=y_enc,
    color=alt.condition("datum.high_and_rising", alt.value(DEEP), alt.value(GREY_DOT)),
    size=alt.condition("datum.high_and_rising", alt.value(260), alt.value(150)),
    tooltip=tooltip)
lab = []
for pos, kw in {"right": dict(align="left", dx=12, dy=0), "left": dict(align="right", dx=-12, dy=0),
                "below": dict(align="center", dx=0, dy=18), "above": dict(align="center", dx=0, dy=-18)}.items():
    lab.append(base.transform_filter(alt.datum.label_pos == pos).mark_text(baseline="middle", fontSize=13, color=BODY, tooltip=False, **kw)
               .encode(x=alt.X("price_yoy_6m_pct:Q", scale=SX), y=alt.Y("gross_yield_pct:Q", scale=SY), text="label:N"))
scatter = alt.layer(quad, vline, hline, corner, corner2, avg_txt, points, *lab).properties(height=560).configure(
    font=FONT, background="#FFFFFF").configure_view(stroke=None).configure_axis(
    labelFont=FONT, titleFont=FONT, gridColor=GRID, domainColor=INK, tickColor=INK, labelColor=MUTED, titleColor=MUTED, labelFontSize=13,
    titleFontSize=12, titleFontWeight=400, labelPadding=6)

st.html(f'<p class="phone-only" style="margin: 0; font-size: 13px; color: {MUTED}">Swipe sideways to see the whole chart.</p>')
with st.container(key="scatter_card"):
    st.altair_chart(scatter, theme=None, width="stretch")
hot = s_seg[s_seg["high_and_rising"]].sort_values("gross_yield_pct", ascending=False)
if len(hot):
    def _hot_name(r):
        t = tile_for(seg, r.area)
        return (t[2] if t else r.community_name) + (" (few projects)" if r.projects_6m < 5 else "")
    hot_rows = "".join(
        f'<div style="display: grid; grid-template-columns: 20px minmax(0, 1fr) auto auto; align-items: baseline; gap: 10px; '
        f'padding: 9px 0; border-bottom: 1px solid {LINE}; break-inside: avoid">'
        f'<span style="font-size: 12px; color: {MUTED}; font-variant-numeric: tabular-nums">{i}</span>'
        f'<span style="font-weight: 500; color: {INK}">{escape(_hot_name(r))}</span>'
        f'<span style="font-weight: 600; color: {DEEP}; font-variant-numeric: tabular-nums">{r.gross_yield_pct:.1f}%</span>'
        f'<span style="width: 64px; text-align: right; color: {BODY}; font-variant-numeric: tabular-nums">{signed_pct(r.price_yoy_6m_pct)}</span></div>'
        for i, r in enumerate(hot.itertuples(), 1))
    st.html(f'<div style="padding-top: 8px"><div style="font-size: 13px; font-weight: 600; letter-spacing: 0.12em; '
            f'text-transform: uppercase; color: {DEEP}; padding-bottom: 6px">The {count_words(len(hot)).lower()}, by gross yield '
            f'<span style="font-weight: 400; letter-spacing: 0; text-transform: none; color: {MUTED}">· yield · 6-month price change</span></div>'
            f'<div style="columns: 2 380px; column-gap: 48px; font-size: 15px">{hot_rows}</div></div>')
st.html(f'<p style="margin: 0; font-size: 13px; color: {MUTED}">Hover over a dot for its numbers. '
        f'{len(measured)} of the {len(s_seg)} {kind} have enough repeat sales to measure price change. '
        f'Dashed lines: no price change, and the {avg_yield:.1f}% average {seg.lower()} yield.</p>'
        f'<div id="outlook" style="height: 40px"></div>')

# ---------------------------------------------------------------- outlook and calculator
SERIES_LABELS = {"DUBAI / Ready / Flat": "Dubai-wide · Ready flats", "DUBAI / Ready / Villa": "Dubai-wide · Ready villas",
                 "DUBAI / Off-Plan / Flat": "Dubai-wide · Off-plan flats",
                 "DUBAI / Off-Plan / Villa": "Dubai-wide · Off-plan villas",
                 "MARSA DUBAI / Ready / Flat": "Dubai Marina · Ready flats"}
series_ids = [s for s in SERIES_LABELS if s in set(D["scenario_summary"]["series_id"])]

left, right = st.columns(2, gap="small")
with left:
    with st.container(key="outlook_card"):
        st.html(eyebrow("12-month outlook", MUTED))
        label_to_id = {SERIES_LABELS[s]: s for s in series_ids}
        sid = label_to_id[st.selectbox("Price index", list(label_to_id), key="series")]
        st.html(f'<h2 style="margin: 4px 0 0; padding: 0; font-family: \'{FONT}\', sans-serif; font-weight: 600; '
                f'font-size: clamp(28px, 2.8vw, 38px); line-height: 1.18; letter-spacing: -0.02em; color: {INK}">'
                f'A base case and a tested range, because no model beat “no change”.</h2>')
        il = D["index_lines"]
        il = il[(il["series_id"] == sid) & (il["month"] >= "2023-01-01")]
        monthly = il[il["line"] == "index (monthly)"].dropna(subset=["value"]).sort_values("month")
        hist = il[il["line"] == "index (3-month avg)"].dropna(subset=["value"]).sort_values("month")
        last_pt = hist.iloc[-1]
        last_month = pd.Timestamp(last_pt["month"])
        SCEN = {"scenario: trend resumes": "Trend resumes", "scenario: flat": "Prices hold",
                "scenario: break continues": "Fall continues"}
        STYLE = {  # name: (colour, width, dashed, point size)
            "Monthly index": ("#A3AAB1", 1.5, False, 14), "3-month average": (INK, 3, False, 26),
            "Trend resumes": (DEEP, 2.5, True, 16), "Prices hold": (MUTED, 2.5, False, 16),
            "Fall continues": (CORAL, 2.5, True, 16)}
        parts = [monthly[["month", "value"]].assign(line="Monthly index"),
                 hist[["month", "value"]].assign(line="3-month average")]
        for key, nm in SCEN.items():
            part = il[il["line"] == key][["month", "value"]]
            parts.append(pd.concat([pd.DataFrame({"month": [last_month], "value": [last_pt["value"]]}), part]).assign(line=nm))
        lines = pd.concat(parts, ignore_index=True)
        lines["vs_now"] = ((lines["value"] / last_pt["value"] - 1) * 100).map(signed_pct)
        end_month = lines["month"].max()

        # Legend (HTML, so it reads like the rest of the page)
        def _swatch(nm):
            colour, width, dashed, _ = STYLE[nm]
            return (f'<span style="display: inline-flex; align-items: center; gap: 6px; white-space: nowrap">'
                    f'<span aria-hidden="true" style="display: inline-block; width: 22px; border-top: {max(width, 2):.0f}px '
                    f'{"dashed" if dashed else "solid"} {colour}"></span>{nm}</span>')
        st.html(f'<div style="display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 13px; color: {BODY}">'
                + "".join(_swatch(nm) for nm in STYLE) + "</div>")

        names, styles = list(STYLE), list(STYLE.values())
        x_end = end_month + pd.DateOffset(months=1)
        xs = alt.Scale(domain=[alt.DateTime(year=2023, month=1, date=1),
                               alt.DateTime(year=x_end.year, month=x_end.month, date=1)])
        ys = alt.Scale(zero=False, padding=16)
        x_enc = alt.X("month:T", title=None, scale=xs, axis=alt.Axis(format="%Y", tickCount="year", grid=False))
        y_enc = alt.Y("value:Q", title="Index, Jan 2020 = 100", scale=ys)
        colour = alt.Color("line:N", scale=alt.Scale(domain=names, range=[s[0] for s in styles]), legend=None)
        hover = alt.selection_point(fields=["month"], nearest=True, on="pointerover", clear="pointerout", empty=False)
        base_o = alt.Chart(lines)
        shade = alt.Chart(pd.DataFrame({"a": [last_month], "b": [end_month]})).mark_rect(
            color="#F2F3EF", tooltip=False).encode(x=alt.X("a:T", scale=xs), x2="b:T")
        line_marks = base_o.mark_line(tooltip=False).encode(
            x=x_enc, y=y_enc, color=colour, detail="line:N",
            strokeWidth=alt.StrokeWidth("line:N", scale=alt.Scale(domain=names, range=[s[1] for s in styles]), legend=None),
            strokeDash=alt.StrokeDash("line:N", scale=alt.Scale(domain=names, range=[[6, 4] if s[2] else [1, 0] for s in styles]),
                                      legend=None))
        rule = base_o.mark_rule(color="#B9C0C6", strokeDash=[3, 3], tooltip=False).encode(x=x_enc).transform_filter(hover)
        pts = base_o.mark_circle(opacity=1).encode(
            x=x_enc, y=y_enc, color=colour,
            size=alt.condition(hover, alt.value(110),
                               alt.Size("line:N", scale=alt.Scale(domain=names, range=[s[3] for s in styles]), legend=None)),
            tooltip=[alt.Tooltip("month:T", format="%b %Y", title="Month"), alt.Tooltip("line:N", title="Line"),
                     alt.Tooltip("value:Q", format=".1f", title="Index"),
                     alt.Tooltip("vs_now:N", title=f"vs {last_month:%b %Y}")]).add_params(hover)
        ends = lines[lines["line"].isin(SCEN.values()) & (lines["month"] == end_month)].copy()
        ends["txt"] = ends["value"].map("{:.1f}".format)
        end_pts = alt.Chart(ends).mark_circle(size=70, opacity=1, tooltip=False).encode(x=x_enc, y=y_enc, color=colour)
        end_lab = alt.Chart(ends).mark_text(align="left", dx=9, fontSize=12, fontWeight=600, tooltip=False).encode(
            x=x_enc, y=y_enc, color=colour, text="txt:N")
        peak = hist.loc[hist["value"].idxmax()]
        marks = pd.DataFrame({"month": [peak["month"]], "value": [peak["value"]],
                              "txt": [f"Peak {peak['value']:.1f} · {peak['month']:%b %Y}"]})
        mark_lab = alt.Chart(marks).mark_text(align="center", dy=-16, fontSize=12, fontWeight=500, color=INK,
                                              tooltip=False).encode(x=x_enc, y=y_enc, text="txt:N")
        outlook = alt.layer(shade, rule, line_marks, pts, end_pts, end_lab, mark_lab).properties(
            height=320, padding={"left": 4, "top": 8, "right": 48, "bottom": 4}).configure(
            font=FONT, background="#FFFFFF").configure_view(stroke=None).configure_axis(
            labelFont=FONT, titleFont=FONT, gridColor=GRID, domainColor=INK, tickColor=INK, labelColor=MUTED, titleColor=MUTED, labelFontSize=12,
            titleFontSize=12, titleFontWeight=400)
        st.altair_chart(outlook, theme=None, width="stretch")
        sc = D["scenario_summary"].set_index(["series_id", "scenario"])["change_12m_pct"]
        chips = [("trend resumes", "Trend resumes", DEEP, "#FFFFFF"), ("flat", "Base case: prices hold", GRID, BODY),
                 ("break continues", "Fall continues", CORAL, "#FFFFFF")]
        st.html('<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">' + "".join(
            f'<div style="background: {bg}; color: {fg}; padding: 14px"><div style="font-size: clamp(20px, 5.5vw, 30px); font-weight: 600; '
            f'line-height: 1; white-space: nowrap">{signed_pct(sc.get((sid, key), float("nan")))}</div>'
            f'<div style="font-size: 13px; padding-top: 6px">{text}</div></div>'
            for key, text, bg, fg in chips) + "</div>")
        st.html(f'<p style="margin: 0; font-size: 13px; color: {MUTED}">Shaded: the next 12 months. Scenarios are '
                f'conditional, not predictions: each shows the outcome if its assumption holds.</p>')

with right:
    with st.container(key="calc_card"):
        st.html('<div id="calc"></div>' + eyebrow("Yield calculator", "#A9AFB6")
                + f'<h2 style="margin: 12px 0 0; padding: 0; font-family: \'{FONT}\', sans-serif; font-weight: 600; '
                  f'font-size: clamp(28px, 2.8vw, 38px); line-height: 1.18; letter-spacing: -0.02em; color: {PAPER}">'
                  f'Pick a community. Enter a price. See the yield you would actually get.</h2>')
        calc_seg = st.segmented_control("Property type", ["Flat", "Villa"], default="Flat", required=True,
                                        key="calc_seg", label_visibility="collapsed")
        options = score[score["segment"] == calc_seg].sort_values("community_name")
        names = options["community_name"].tolist()
        preferred = "Dubai Marina" if calc_seg == "Flat" else "Dubai Hills Estate"
        f1, f2, f3 = st.columns([1.2, 0.7, 1.2])
        name = f1.selectbox("Community", names, index=names.index(preferred) if preferred in names else 0,
                            key=f"comm_{calc_seg}")
        row = options[options["community_name"] == name].iloc[0]
        size = f2.number_input("Size (sqm)", min_value=15, max_value=2000,
                               value=75 if calc_seg == "Flat" else 250, step=5, key=f"size_{calc_seg}")
        median_value = int(round(row["ready_aed_per_sqm_6m"] * size, -4))
        # Keyed per community, so a price you typed survives a change of size.
        price = f3.number_input("Price (AED)", min_value=100_000, max_value=100_000_000, value=median_value,
                                step=50_000, key=f"price_{calc_seg}_{row['area']}",
                                help="Starts at the community's median Ready price per sqm × your size.")
        with st.expander("Running costs (optional, for net yield)"):
            r1, r2, r3 = st.columns(3)
            svc = r1.number_input("Service charge (AED/sqm/yr)", 0.0, 200.0, 0.0, 1.0)
            vac = r2.number_input("Vacancy (% of year)", 0.0, 50.0, 0.0, 1.0)
            oth = r3.number_input("Other costs (% of rent)", 0.0, 50.0, 0.0, 1.0)
        est = estimate_yield(row["gross_yield_pct"], row["ready_aed_per_sqm_6m"], size, price, svc, vac, oth)
        has_costs = svc > 0 or vac > 0 or oth > 0
        series = scenario_series_for(row["area"], calc_seg)
        vals = scenario_values(D["scenario_summary"], series, price).set_index("scenario")["value_in_12m_aed"]
        pv = est.price_vs_market_pct
        price_note = ("" if abs(pv) < 1 else
                      f"Your price is {abs(pv):.0f}% {'above' if pv > 0 else 'below'} the community median for this "
                      f"size (AED {est.market_value:,.0f}), so your yield is {'lower' if pv > 0 else 'higher'} than "
                      f"the community's {row['gross_yield_pct']:.1f}%.")
        net_box = (f'<div style="background: #1C2026; padding: 16px; grid-column: 1 / -1"><div style="font-size: 13px; '
                   f'color: #A9AFB6">Net yield after your costs</div><div style="font-size: 28px; font-weight: 600; '
                   f'line-height: 1.1; color: {PAPER}">{est.net_yield_pct:.1f}%</div></div>') if has_costs else ""
        rows = [("trend resumes", "In 12 months if the trend resumes"), ("flat", "If prices hold"),
                ("break continues", "If the fall continues")]
        st.html(f"""
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px">
  <div style="background: #1C2026; padding: 16px"><div style="font-size: 13px; color: #A9AFB6">Market rent a year, {size:,.0f} sqm</div><div style="font-size: clamp(22px, 2.6vw, 36px); font-weight: 600; line-height: 1.15; color: {PAPER}; white-space: nowrap">AED {est.est_annual_rent:,.0f}</div><div style="font-size: 12px; color: #A9AFB6; padding-top: 4px">AED {est.est_annual_rent / 12:,.0f} a month</div></div>
  <div style="background: #E6EEF2; padding: 16px"><div style="font-size: 13px; color: #2C4A5E">Gross yield on AED {price:,.0f}</div><div style="font-size: clamp(26px, 2.6vw, 36px); font-weight: 600; line-height: 1.15; color: #0B1B26">{est.gross_yield_pct:.1f}%</div><div style="font-size: 12px; color: #2C4A5E; padding-top: 4px">Community average {row['gross_yield_pct']:.1f}%</div></div>
  {net_box}
</div>
{f'<p style="margin: 12px 0 0; font-size: 14px; color: #D4D8DC">{price_note}</p>' if price_note else ''}
<div style="display: flex; flex-direction: column; font-size: 15px; margin-top: 8px">
""" + "".join(
            f'<div style="display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; '
            f'border-bottom: 1px solid #2C3137"><span style="color: #A9AFB6">{text}</span>'
            f'<span style="font-weight: 500; color: {PAPER}; white-space: nowrap">AED {vals[key]:,.0f}</span></div>'
            for key, text in rows if key in vals) + f"""
</div>
<p style="margin: 10px 0 0; font-size: 12px; color: #A9AFB6">Rent comes from the community and the size, not from what you pay: a higher price buys the same rent, so it lowers your yield. Rent = the community's gross yield × its median price per sqm × your size; a specific unit depends on building, floor and view. 12-month values use the {escape(SERIES_LABELS.get(series, series))} index.</p>
""")

# ---------------------------------------------------------------- method
bt = backtest_table(D["backtest_summary"], sid)
body_rows = []
for (period, h), r in bt.iterrows():
    best, worst = r.min(), r.max()
    cells = []
    for m in bt.columns:
        v = r[m]
        style = f"font-weight: 600; color: {DEEP}" if v == best else (f"color: {CORAL}" if v >= 2 * best and v == worst else "")
        cells.append(f'<td style="padding: 10px 12px; text-align: right; {style}">{v:.1f}</td>')
    label = ("Normal years" if period == "normal" else "After the 2026 break") + f", {h} months ahead"
    body_rows.append(f'<tr style="border-bottom: 1px solid {LINE}"><th scope="row" style="padding: 10px 12px 10px 0; '
                     f'font-weight: 400; text-align: left">{label}</th>{"".join(cells)}</tr>')
heads = "".join(f'<th scope="col" style="padding: 10px 12px; font-weight: 500; text-align: right">{MODEL_NAMES[m]}</th>'
                for m in bt.columns)

st.html(f"""
<section id="method" style="padding: 64px 0 24px">
<h2 style="margin: 0 0 20px; padding: 0; font-family: '{FONT}', sans-serif; font-weight: 600; font-size: clamp(28px, 2.8vw, 38px); letter-spacing: -0.02em; color: {INK}">How the numbers were made</h2>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap: 24px 40px; font-size: 15px; line-height: 1.6; color: {BODY}; font-weight: 300">
<div style="border-top: 2px solid {INK}; padding-top: 14px"><div style="font-weight: 600; color: {INK}; margin-bottom: 6px">Like-for-like yield</div>New-lease rent per sqm divided by Ready sale price per sqm, matched by community, type and size band. A naive version was off by up to 1.9 points.</div>
<div style="border-top: 2px solid {INK}; padding-top: 14px"><div style="font-weight: 600; color: {INK}; margin-bottom: 6px">Same-project prices</div>Momentum and the price index follow the same projects, so new launches do not pass for growth.</div>
<div style="border-top: 2px solid {INK}; padding-top: 14px"><div style="font-weight: 600; color: {INK}; margin-bottom: 6px">Backtested outlook</div>SARIMA, “no change” and trend models were tested every 3 months from 2018. None held up across the 2026 break.</div>
</div>
<div style="margin-top: 32px; overflow-x: auto">
<table class="dym-method-table" style="width: 100%; min-width: 560px; border-collapse: collapse; font-size: 14px; font-variant-numeric: tabular-nums; color: {INK}">
<caption style="text-align: left; font-weight: 600; padding-bottom: 10px; font-size: 15px">Average forecast error, {escape(SERIES_LABELS.get(sid, sid))} (%). Lower is better.</caption>
<thead><tr style="border-bottom: 2px solid {INK}; text-align: left"><th scope="col" style="padding: 10px 12px 10px 0; font-weight: 500">Period and horizon</th>{heads}</tr></thead>
<tbody>{"".join(body_rows)}</tbody>
</table>
</div>
<p style="margin: 20px 0 0; font-size: 13px; color: {MUTED}">Limits: yields are gross, before service charges, vacancy and fees. Rent data starts in Jan 2026. Scenarios exist only for Dubai-wide series and Dubai Marina flats; other communities have under 8 years of monthly history.</p>
</section>
<footer style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 24px; padding: 24px 0 8px; border-top: 1px solid {LINE}; font-size: 13px; color: {MUTED}">
<div>Source: Dubai Land Department sales and rental contracts, to {as_of:%B %Y}</div>
<div>Not investment advice</div>
</footer>
""")
