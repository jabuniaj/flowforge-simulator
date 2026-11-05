from streamlit.testing.v1 import AppTest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_scenarios_and_export():
    app = AppTest.from_file(APP,default_timeout=30).run()
    assert not app.exception
    for scenario in ("Demand surge (+40%)", "Two packing employees absent", "Packing equipment failure", "Custom stress test"):
        app.selectbox[0].select(scenario).run()
        assert not app.exception
        assert len(app.metric) == 4


def test_staffing_search():
    app = AppTest.from_file(APP,default_timeout=60).run()
    app.button[0].click().run(timeout=60)
    assert not app.exception
    assert any("Selected picking" in item.value for item in app.markdown)
