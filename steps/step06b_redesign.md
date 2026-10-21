# Step 6b: Redesign the app as "Dubai Yield Map"

**Goal:** replace the 4-tab app from step 6 with the one-page design you approved (reference: https://claude.ai/artifact/HYcnWNJx1WbNveSUP69kU2). Same repo, same Streamlit link.

## What changed

**The page, top to bottom**
1. **Hero:** "The lights are on the water. The yield is inland." with the yield legend.
2. **Tile map** of 37 flat or 15 villa communities, coloured by gross yield. The Gulf is at the top, inland at the bottom. A dark tile with a dot means yield above average and prices still rising.
3. **Four market cards:** sales change, price index, distance below peak, off-plan premium. They are computed from the data, not typed in.
4. **Scatter:** yield vs 6-month price change, with the "above average and rising" corner shaded.
5. **12-month outlook:** pick one of the 5 series; base case plus downside and upside scenarios.
6. **Yield calculator:** Flat/Villa, community, size, price, optional running costs (net yield).
7. **Method:** backtest table for the selected series, and the limits.

**One Flats / Villas switch** drives both the map and the scatter. There are two copies of the button (above the map and above the scatter) and they stay in sync.

**Files**
```
app/streamlit_app.py     rewritten
app/calc.py              + market cards, yield colour bands, "above average and rising" rule, text helpers
app/tile_layout.py       new: where each community sits on the map, and its label
app/tests/               14 tests (was 7): maths, map layout (no overlaps, every community placed), app clicks
.streamlit/config.toml   new colours and fonts
python/08_prepare_app_data.py   now also copies monthly_rents.csv
.gitignore               bug fix, see below
```

## Two fixes you need to know about

**1. Community names (reference/area_names.csv).** I checked every name marked `check` against DLD and developer sources.
- **Wadi Al Safa 3 and 5 were swapped.** WAS 3 is Majan; WAS 5 is Dubailand Residence Complex.
  - So the 9.0% / +2.3% flat area is **Residence Complex**, and Majan is 7.3% / +6.6%.
- **Renamed:** Al Barsha South 2 is Dubai Science Park (not Al Barari). Warsan 4 is International City Phase 2. Jebel Ali Industrial 2 is Downtown Jebel Ali. Al Hebiah 2 is Studio City. Al Thanyah 3 is The Views.
- **Areas that hold several communities keep a neutral name.** The top villa point on the scatter is now labelled **"Wadi Al Safa 7"** (6.0%, +15.8%). Earlier I called it Rukan; that area also contains Arabian Ranches 2 and Serena, so naming one of them would overclaim.
- Your Power BI report picks up the new names the next time you refresh it after rerunning step 07.

**2. `.gitignore` was hiding the app's data.** The old line `data/` matches *any* folder called `data`, including `app/data/`. Pushed like that, the live app would have no CSVs and crash on load. It is now `/data/`, which only matches the top-level folder.

## Run it on your laptop

From the project folder, venv active:

```
python python/07_export_powerbi.py
python python/08_prepare_app_data.py
pip install -r app/requirements.txt pytest
pytest app/tests -q
streamlit run app/streamlit_app.py
```

- Step 07 must be rerun because the names changed. Step 08 must be rerun because the app now needs `monthly_rents.csv`.
- **Expected test result:** `17 passed`.
- **Step 08 should print 6 files**, ending with `copied monthly_rents.csv`.

**Check in the browser**
- Flats view: 37 tiles; Palm Jumeirah and Creek Harbour sit in the Gulf row.
- Click **Villas**: the map and scatter both switch, and the scatter heading says "Two villa communities…".
- Calculator: Flat, Dubai Marina, default size and price gives about **5.3%** gross yield. Raise the price 10% and it falls to about 4.8%.
- Narrow the browser window to phone width: the map and scatter scroll sideways with a "Swipe sideways" hint.

## Push the update

```
git add -A
git status
git commit -m "Redesign app as Dubai Yield Map; fix area names and .gitignore"
git push
```

In `git status`, **all 6 files in `app/data/` must appear**, and nothing under the top-level `data/` may appear. Streamlit Cloud redeploys on push; the **app-ci** check on GitHub should go green.

## Known limits

- The map is schematic: positions are roughly right (west to east, coast to inland), not to scale. The page says so.
- Only communities with at least 50 leases and 50 sales appear. That is why there is no waterfront villa tile: none passes the threshold.

## Round 2 fixes (after your first local run)

| What you saw | Cause | Fix |
|---|---|---|
| Headline squeezed into 5 lines beside an empty right side | The two-column hero gave the headline half the width (the reference had the same flaw) | Headline spans the page on two lines, one sentence each; text and legend sit below it |
| Scatter hover showed a box with `x 0, y 6.89, x2 15, y2 10` | The shaded "high yield, rising" area had Streamlit's default tooltip | Tooltips switched off on everything except the dots; the chart's download/fullscreen icons hidden too |
| Outlook chart had one line and no points | It drew only the 3-month average | Both lines (monthly index and 3-month average), a dot per month, hover tooltips with the value and change vs Sep 2026, the peak labelled, and each scenario's end value labelled |
| Calculator rent did not change | Rent comes from community and size, so it **should not** change with price; only the yield does. Separately, changing the size reset your typed price | Price now stays when you change size; the boxes say "Market rent a year, 75 sqm", show the monthly rent, and a note explains why price changes the yield, not the rent |
| Method table had no numbers | Your pipeline saves model names as `naive`, `drift`, `sarima`; the app looked for `Naive`, `Drift`, `SARIMA` | Names now match in any case; a test covers both spellings |
| Menu scrolled away | It was part of the page | Fixed bar that stays at the top; section links land below it |

Also fixed: the outlook and calculator cards are now the same height; the twelve "high yield, rising" communities are listed by name under the scatter (half of them had no label); on phones the menu fits on one line and the method table fits the screen without sideways scrolling.
