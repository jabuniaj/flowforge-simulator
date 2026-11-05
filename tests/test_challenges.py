import pytest
from streamlit.testing.v1 import AppTest
from pathlib import Path
from flowforge.challenges import MISSIONS, build_plan, evaluate
from dataclasses import asdict
import json


def test_mobile_mission_rules_match_python_source():
    path=Path(__file__).resolve().parents[1]/'mobile/missions.json'
    assert json.loads(path.read_text())==json.loads(json.dumps([asdict(m) for m in MISSIONS]))


@pytest.mark.parametrize("mission",MISSIONS)
def test_reference_plan_is_feasible_and_solves_mission(mission):
    r=evaluate(mission,mission.reference_staff,mission.reference_bench,mission.reference_repair)
    assert r['extra_cost']<=mission.budget
    assert r['successes']>=8
    assert r['gain']>0


def test_constraints_prevent_fictitious_workers_or_spending():
    with pytest.raises(ValueError): build_plan(MISSIONS[0],(4,3,2))
    with pytest.raises(ValueError): build_plan(MISSIONS[2],(5,3,2),True,True)
    with pytest.raises(ValueError): build_plan(MISSIONS[0],(3,2,2),True)


def test_challenge_learning_loop():
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=30).run()
    assert not app.exception
    assert any('rescue the shift' in x.value for x in app.title)
    # Move one picker to packing; keep the same team.
    app.number_input(key='callout_staff0').set_value(3)
    app.number_input(key='callout_staff1').set_value(2)
    app.run()
    next(b for b in app.button if b.label=='Run my shift →').click().run()
    assert not app.exception
    assert any('Mission solved' in x.value for x in app.success)
    assert len(app.session_state['history']['callout'])==1
    app.radio(key='section').set_value('How to play').run()
    assert not app.exception


def test_other_missions_and_budget_feedback():
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=30).run()
    app.radio(key='mission').set_value(2).run()
    app.checkbox[0].check()
    app.checkbox[1].check().run()
    assert not app.exception
    assert next(b for b in app.button if b.label=='Run my shift →').disabled
