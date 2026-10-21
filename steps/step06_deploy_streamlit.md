# Step 6: Deploy a public Streamlit app

**Goal:** a link anyone can open (a recruiter on their phone, an interviewer before the call) that shows the project's answer and lets them try it. Your Power BI report can't do this without a work account.

**What the app adds beyond the dashboard:** a **yield calculator**.
- Pick a community, a size and a price.
- It estimates the annual rent and your gross and net yield *on the price you'd pay*.
- It also shows what the home could be worth in 12 months under the three scenarios.

The other three tabs (Where to invest, 12-month outlook, Method and limits) repeat the dashboard's answers for people without Power BI.

## What's in the folder

```
app/
  streamlit_app.py        the app (4 tabs)
  calc.py                 the maths, kept separate so it can be unit-tested
  requirements.txt        only what the app needs (streamlit, pandas, altair)
  data/                   5 small CSVs, filled by python/08_prepare_app_data.py
  tests/
    test_calc.py          6 tests of the yield and scenario maths
    test_app.py           runs the whole app headless and clicks through it
.streamlit/config.toml    colours matching the Power BI report
.github/workflows/app-ci.yml   runs the tests on GitHub every time you push app changes
.gitignore                keeps data/ (DuckDB, raw files) off GitHub
python/08_prepare_app_data.py
```

I ran the app and its tests on the numbers from your finished `.pbix`: all 7 tests pass, and I checked screenshots of every tab.

## 6.1 Run it on your laptop first

In the VS Code terminal, from the project folder, with your venv active:

```
pip install -r app/requirements.txt pytest
python python/08_prepare_app_data.py
streamlit run app/streamlit_app.py
```

- The browser should open at `http://localhost:8501`.
- Click through all 4 tabs, then stop the app with **Ctrl+C**.
- Then run the tests with `pytest app/tests -q`. Expected: `7 passed`.

Try the calculator with these inputs:
- **Inputs:** Flat, Dubai Marina, 75 sqm, at the default price.
- **Expected:** the gross yield should equal Marina's community yield (5.3%). Raise the price by 10% and the yield should fall to about 4.8%.
- **Why it falls:** you paid more, but the rent didn't change.

## 6.2 Put the project on GitHub

1. **Create the repo.** On github.com: **New repository**.
   - Name it `dubai-property-intelligence`.
   - Make it **Public**. Streamlit's free tier needs public repos, and recruiters need to see the code.
   - Don't add a README; the project already has one.
2. **Push the project.** In the VS Code terminal, from the project folder:

```
git init
git add .
git commit -m "Dubai property market intelligence: pipeline, Power BI report, Streamlit app"
git branch -M main
git remote add origin https://github.com/<your-username>/dubai-property-intelligence.git
git push -u origin main
```

3. **Check before you push.** Run `git status` after `git add .`.
   - **`data/` must not appear.** `.gitignore` excludes it; your DuckDB file and raw downloads stay local.
   - **`app/data/*.csv` must appear.** The app needs those 5 small files.
4. **Watch the first CI run.** On GitHub, open the **Actions** tab. A green tick on **app-ci** means the tests passed on a clean machine. That's a credible extra line for an interview.

## 6.3 Deploy on Streamlit Community Cloud (free)

1. **Sign in.** Go to **share.streamlit.io** and sign in with your GitHub account.
2. **Create the app.** Click **Create app**, then **Deploy a public app from GitHub**, and fill in:
   - **Repository:** `<your-username>/dubai-property-intelligence`
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py`
   - **App URL:** pick something readable, such as `dubai-property-yield`
   - **Advanced settings:** Python **3.12**
3. **Deploy.** The first build takes a few minutes. It installs `app/requirements.txt`, which sits next to the main file, so the heavy pipeline packages (statsmodels, duckdb) are never installed.
4. **Updates.** Every later `git push` redeploys the app automatically.

**One limit of the free tier:** apps go to sleep after a period without visitors, and the first visitor then waits about 30 seconds while it wakes up. Open it yourself before an interview.

## 6.4 Updating the numbers later

When you add new DLD months:
1. Rerun steps 02 → 07 as usual.
2. Run `python python/08_prepare_app_data.py`.
3. Commit the changed CSVs in `app/data/` and push.

The app and CI pick them up automatically.

## 6.5 How to describe it, without overselling

**Resume line (accurate):**
> Built and deployed a public Streamlit app (yield calculator + 12-month scenarios) with unit tests and GitHub Actions CI; live at <URL>.

**Don't write** "production-level deployment" or list Gradio or FastAPI for this project.
- This is a hosted demo app, not a production service. There is no API, container, monitoring or scheduled pipeline.
- If an interviewer asks what production would add, here's the honest answer: "Automating the monthly data refresh, serving the scorecard through an API, containerising it, and monitoring data freshness."
- That's a strong answer, and it's the plan for the next project.

## 6.6 Known limits shown in the app

- **The calculator's rent is an estimate:** community gross yield × the community's median price per sqm × your size. It doesn't know your building, floor or view.
- **Net yield** only differs from gross if you enter your own running costs. The defaults are 0 because service charges vary too much between buildings for a single default to be honest.
- **12-month values** use the Dubai-wide Ready series for your segment, or Dubai Marina's own series for Marina flats. No other community has enough history for scenarios.
