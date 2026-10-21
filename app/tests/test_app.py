"""Smoke test: the app renders and its controls work on the committed data."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "streamlit_app.py"
DATA = Path(__file__).parents[1] / "data" / "community_scorecard.csv"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="app/data not prepared (run python/08_prepare_app_data.py)")


def run_app():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, at.exception
    return at


def test_app_renders_flats_by_default():
    at = run_app()
    assert at.session_state.segment == "Flats"
    assert at.button_group(key="seg_map").value == "Flats"


def test_both_switches_stay_in_sync():
    at = run_app()
    at.button_group(key="seg_map").set_value("Villas").run()
    assert not at.exception, at.exception
    assert at.session_state.segment == "Villas"
    assert at.button_group(key="seg_scatter").value == "Villas"
    at.button_group(key="seg_scatter").set_value("Flats").run()
    assert at.button_group(key="seg_map").value == "Flats"


def test_calculator_and_outlook_inputs():
    at = run_app()
    at.button_group(key="calc_seg").set_value("Villa").run()
    assert not at.exception, at.exception
    comm = at.selectbox(key="comm_Villa")
    comm.set_value(comm.options[0]).run()
    assert not at.exception, at.exception
    at.number_input(key="size_Villa").set_value(300).run()
    for i in range(len(at.selectbox(key="series").options)):
        at.selectbox(key="series").select_index(i).run()
        assert not at.exception, at.exception


def _html(at):
    return " ".join(h.proto.body for h in at.get("html"))


def test_method_table_shows_error_values():
    at = run_app()
    page = _html(at)
    assert "No change" in page and "SARIMA" in page
    # 4 rows x 3 models of numbers in the table
    import re
    table = page[page.index("Average forecast error"):page.index("</table>")]
    assert len(re.findall(r'<td[^>]*>\d+\.\d</td>', table)) == 12


def test_calculator_rent_follows_size_and_keeps_typed_price():
    at = run_app()
    price_key = next(n.key for n in at.number_input if n.key and n.key.startswith("price_Flat"))
    at.number_input(key=price_key).set_value(1_500_000).run()
    before = _html(at)
    at.number_input(key="size_Flat").set_value(100).run()
    assert not at.exception, at.exception
    assert at.number_input(key=price_key).value == 1_500_000
    after = _html(at)
    import re
    rent = lambda s: re.search(r"Market rent a year.*?AED ([\d,]+)", s).group(1)
    assert rent(before) != rent(after)
