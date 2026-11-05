"""Synthetic teaching missions. Feedback comes from simulated decisions."""
from dataclasses import dataclass, replace
from statistics import mean
from .model import Shift, STATIONS, replicate

SEEDS = tuple(range(410,420))


@dataclass(frozen=True)
class Mission:
    id: str
    title: str
    subtitle: str
    brief: str
    goal: str
    config: Shift
    target: int
    budget: int
    bench_cost: int
    repair_cost: int
    repaired_duration: int
    hint: str
    lesson: str
    reference_staff: tuple
    reference_bench: bool = False
    reference_repair: bool = False


MISSIONS = (
    Mission("callout", "The missing packers", "01 / Move people, not the budget",
        "Two packers called out. Seven people are here, and orders keep arriving. "
        "You can move workers between stations, but nobody else can come in today.",
        "Complete at least 270 of 500 orders in at least 8 of 10 simulated shifts.",
        Shift(staff=(4,1,2)),270,0,0,0,0,
        "Compare each station's processing time and worker count. Which station feeds work faster than the next can handle it?",
        "The station with the longest task is not always the bottleneck. Staffing changes the rate. "
        "Once packing recovers, picking can become the next constraint.",(3,2,2)),
    Mission("bench", "People cannot fix everything", "02 / Find the physical constraint",
        "Nine people showed up, but only one packing bench works. There is a spare bench "
        "available to rent for the shift. Decide whether moving people is enough.",
        "Complete at least 300 of 500 orders in at least 8 of 10 simulated shifts. Spend no more than $40 extra.",
        Shift(equipment=(12,1,2)),300,40,40,0,0,
        "How many people can actually pack at the same time? Extra workers cannot share a single occupied bench.",
        "People and equipment are joint constraints. A worker assigned to a station is not necessarily a worker who can work.",
        (4,3,2),True),
    Mission("repair", "The two-hour breakdown", "03 / Buy the right recovery",
        "A packing failure will stop the whole station from minute 180 to 300. "
        "You have $60: rent one bench for $40, or pay $60 for a repair crew that cuts the stop to 30 minutes. "
        "A spare bench does not bypass this station-wide failure.",
        "Complete at least 420 of 650 orders in at least 8 of 10 simulated shifts. Spend no more than $60 extra.",
        Shift(orders=650,staff=(5,3,2),outage_duration=120),420,60,40,60,30,
        "A bench adds capacity while the station is running. A repair changes how long it cannot run. Which loss are you trying to fix?",
        "Capacity and availability solve different problems. Spend against the cause of the queue, not its most visible symptom.",
        (5,3,2),False,True),
)


def build_plan(mission, staff, bench=False, repair=False):
    staff = tuple(staff)
    if len(staff)!=3 or any(not isinstance(x,int) or not 0<=x<=12 for x in staff):
        raise ValueError("Use 0–12 whole workers per station.")
    if sum(staff)!=sum(mission.config.staff):
        raise ValueError(f"Assign exactly {sum(mission.config.staff)} workers.")
    if bench and not mission.bench_cost:
        raise ValueError("A spare bench is not available in this mission.")
    if repair and not mission.repair_cost:
        raise ValueError("A repair crew is not available in this mission.")
    cost = mission.bench_cost*bool(bench)+mission.repair_cost*bool(repair)
    if cost>mission.budget:
        raise ValueError("This plan exceeds the extra spending budget.")
    eq = mission.config.equipment
    config = replace(mission.config,staff=staff,
        equipment=(eq[0],eq[1]+int(bench),eq[2]),
        outage_duration=mission.repaired_duration if repair else mission.config.outage_duration)
    return config,cost


def evaluate(mission, staff, bench=False, repair=False):
    config,cost = build_plan(mission,staff,bench,repair)
    before = replicate(mission.config,SEEDS)
    after = replicate(config,SEEDS)
    baseline_mean = mean(r["completed"] for r in before)
    plan_mean = mean(r["completed"] for r in after)
    queue_means = [mean(r["stations"][i]["average_queue"] for r in before) for i in range(3)]
    maximum = max(queue_means)
    pressure = [STATIONS[i] for i,v in enumerate(queue_means) if abs(v-maximum)<1e-8]
    return {"config":config,"extra_cost":cost,"before":before,"after":after,
            "baseline_mean":baseline_mean,"plan_mean":plan_mean,"gain":plan_mean-baseline_mean,
            "successes":sum(r["completed"]>=mission.target for r in after),
            "pressure":pressure,"queue_means":queue_means}
