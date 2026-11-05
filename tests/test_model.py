from dataclasses import replace
import pytest
from flowforge.model import Shift, capacity, simulate, optimize
from random import Random


def test_tied_capacity():
    r = capacity(Shift(staff=(5, 3, 2)))
    assert list(r["capacity"].values()) == [480]*3
    assert len(r["bottlenecks"]) == 3


def test_empty_shift():
    r = simulate(Shift(orders=0))
    assert r["completed"] == r["unfinished"] == 0
    assert r["cost_per_order"] is None


def test_single_order_known_service():
    r = simulate(Shift(orders=1, minutes=1000, cv=0), seed=1)
    assert r["completed"] == 1
    assert r["cycle_minutes"] == pytest.approx(10)
    assert r["waiting_minutes"] == 0


def test_conservation_and_utilization():
    c = Shift()
    r = simulate(c)
    assert r["completed"] + r["unfinished"] == c.orders
    for s in r["stations"]:
        assert 0 <= s["worker_utilization"] <= 1
        assert 0 <= s["workstation_utilization"] <= 1
        assert s["average_queue"] >= 0


@pytest.mark.parametrize("staff", [(0,3,2),(4,0,2),(4,3,0)])
def test_zero_staff(staff):
    assert simulate(Shift(staff=staff))["completed"] == 0


def test_reproducible():
    assert simulate(Shift(), 7) == simulate(Shift(), 7)


def test_full_outage():
    c = Shift(outage_start=0, outage_duration=480)
    assert simulate(c)["completed"] == 0
    assert capacity(c)["capacity"]["Packing"] == 0


def test_downtime_cannot_improve_deterministic_output():
    c = Shift(cv=0)
    assert simulate(replace(c, outage_duration=90))["completed"] <= simulate(c)["completed"]


def test_pause_resume_and_busy_accounting():
    arrival = Random(1).uniform(0,100)
    c = Shift(orders=1, minutes=100, cv=0, staff=(1,1,1),
              equipment=(1,1,1), outage_start=arrival+6, outage_duration=10)
    r = simulate(c,seed=1)
    assert r["cycle_minutes"] == pytest.approx(20)
    assert r["waiting_minutes"] == pytest.approx(10)
    assert [s["worker_utilization"] for s in r["stations"]] == pytest.approx([.05,.03,.02])


def test_finite_horizon_service_is_censored():
    c = Shift(orders=1, minutes=10, cv=0, times=(20.,3.,2.),staff=(1,1,1))
    r = simulate(c,seed=1)
    assert r["completed"] == 0
    assert r["stations"][0]["worker_utilization"] == pytest.approx(1-Random(1).random())


def test_equipment_caps_processing():
    c = Shift(cv=0,staff=(4,3,2),equipment=(1,3,2))
    assert simulate(c)["completed"] <= 96


def test_optimizer_constraints_and_ranking():
    c = Shift(orders=30, staff=(2,1,1), minutes=60)
    rows = optimize(c, seeds=(1,), limit=3)
    assert all(sum(r["staff"]) == 4 and min(r["staff"]) >= 1 for r in rows)
    baseline = next(r for r in rows if r["staff"] == c.staff)
    assert rows[0]["mean_completed"] >= baseline["mean_completed"]


@pytest.mark.parametrize("kwargs", [{"times": (0,3,2)}, {"minutes": 0}, {"orders": -1},
    {"staff": (-1,2,3)}, {"wage": float('nan')}, {"equipment": (1,2)}])
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        Shift(**kwargs)
