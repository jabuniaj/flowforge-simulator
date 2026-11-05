"""Finite-shift simulation. All times are minutes; all data are synthetic."""
from dataclasses import dataclass, replace
from math import floor, isfinite, isclose
from random import Random
from statistics import mean
import simpy

STATIONS = ("Picking", "Packing", "Shipping")


@dataclass(frozen=True)
class Shift:
    orders: int = 500
    minutes: float = 480
    staff: tuple = (4, 3, 2)
    times: tuple = (5., 3., 2.)
    equipment: tuple = (12, 3, 2)
    wage: float = 20.
    cv: float = .25
    outage_station: int = 1
    outage_start: float = 180.
    outage_duration: float = 0.

    def __post_init__(self):
        if not isinstance(self.orders, int) or not 0 <= self.orders <= 10000:
            raise ValueError("Orders must be an integer from 0 to 10000")
        if not isfinite(self.minutes) or self.minutes <= 0:
            raise ValueError("Shift length must be positive and finite")
        for values in (self.staff, self.times, self.equipment):
            if len(values) != 3:
                raise ValueError("Three stations are required")
        if any(not isinstance(x, int) or x < 0 for x in self.staff + self.equipment):
            raise ValueError("Staff and equipment must be nonnegative integers")
        if any(not isfinite(x) or x <= 0 for x in self.times):
            raise ValueError("Processing times must be positive and finite")
        if any(not isfinite(x) or x < 0 for x in (self.wage, self.cv, self.outage_start, self.outage_duration)):
            raise ValueError("Costs, variability and downtime must be finite and nonnegative")
        if self.outage_station not in range(3):
            raise ValueError("Unknown outage station")


def capacity(config):
    available = [config.minutes] * 3
    available[config.outage_station] -= min(config.outage_duration, max(0, config.minutes-config.outage_start))
    caps = [min(w, e)*m/t for w, e, m, t in zip(config.staff, config.equipment, available, config.times)]
    tight = min(caps)
    return {"capacity": dict(zip(STATIONS, map(floor, caps))),
            "bottlenecks": [s for s, c in zip(STATIONS, caps) if isclose(c, tight, rel_tol=1e-9, abs_tol=1e-9)],
            "nominal_completed": min(config.orders, floor(tight))}


def simulate(config, seed=42):
    """FCFS pooled workers, one workstation per active worker, pause/resume outage.

    Separate per-order random streams preserve common random numbers across
    staffing alternatives. Orders arrive uniformly conditional on a fixed count.
    Completion at exactly shift end counts. No overtime or drain-down.
    """
    env = simpy.Environment()
    slots = [min(w, e) for w, e in zip(config.staff, config.equipment)]
    resources = [simpy.Resource(env, capacity=max(1, n)) for n in slots]
    rng = Random(seed)
    arrivals = sorted(rng.uniform(0, config.minutes) for _ in range(config.orders))
    busy = [0.] * 3
    queue_area = [0.] * 3
    queue_peak = [0] * 3
    queue = [0] * 3
    last = [0.] * 3
    waits = [0.] * 3
    starts = [0] * 3
    records = []
    trace = []
    completed = []

    def change_queue(i, delta):
        queue_area[i] += queue[i]*(env.now-last[i])
        last[i] = env.now
        queue[i] += delta
        queue_peak[i] = max(queue_peak[i], queue[i])

    def order(oid, arrival):
        yield env.timeout(arrival)
        total_wait = 0.
        for i, resource in enumerate(resources):
            entered = env.now
            change_queue(i, 1)
            if slots[i] == 0:
                return
            with resource.request() as req:
                yield req
                change_queue(i, -1)
                delay = env.now-entered
                waits[i] += delay
                starts[i] += 1
                total_wait += delay
                r = Random(seed*1000003 + oid*7+i+1)
                duration = (r.gammavariate(1/config.cv**2, config.times[i]*config.cv**2)
                            if config.cv else config.times[i])
                while duration > 1e-10:
                    start = config.outage_start
                    end = start+config.outage_duration
                    if i == config.outage_station and start <= env.now < end:
                        pause = end-env.now
                        total_wait += min(pause, max(0, config.minutes-env.now))
                        yield env.timeout(pause)
                    chunk = duration
                    if i == config.outage_station and env.now < start:
                        chunk = min(chunk, start-env.now)
                    busy[i] += max(0, min(chunk, config.minutes-env.now))
                    yield env.timeout(chunk)
                    duration -= chunk
        completed.append(env.now-arrival)
        records.append({"order": oid, "arrival": arrival, "completion": env.now,
                        "cycle_minutes": env.now-arrival, "waiting_minutes": total_wait})

    def monitor():
        while env.now < config.minutes:
            trace.append({"minute": env.now, **{s: queue[i] for i, s in enumerate(STATIONS)},
                          "completed": len(completed)})
            yield env.timeout(5)

    for oid, arrival in enumerate(arrivals):
        env.process(order(oid, arrival))
    env.process(monitor())
    while env.peek() <= config.minutes:
        env.step()
    for i in range(3):
        queue_area[i] += queue[i]*(config.minutes-last[i])
    count = len(completed)
    labor = sum(config.staff)*config.minutes/60*config.wage
    stations = [{"station": s, "workers": config.staff[i], "workstations": config.equipment[i],
                 "worker_utilization": busy[i]/(config.staff[i]*config.minutes) if config.staff[i] else 0,
                 "workstation_utilization": busy[i]/(config.equipment[i]*config.minutes) if config.equipment[i] else 0,
                 "average_queue": queue_area[i]/config.minutes, "peak_queue": queue_peak[i],
                 "average_wait_started": waits[i]/starts[i] if starts[i] else None,
                 "queue_at_close": queue[i]} for i, s in enumerate(STATIONS)]
    return {"completed": count, "unfinished": config.orders-count,
            "throughput_per_hour": count/(config.minutes/60),
            "cycle_minutes": mean(completed) if completed else None,
            "waiting_minutes": mean(r["waiting_minutes"] for r in records) if records else None,
            "labor_cost": labor, "cost_per_order": labor/count if count else None,
            "stations": stations, "trace": trace, "orders": records}


def replicate(config, seeds):
    return [simulate(config, seed) for seed in seeds]


def optimize(config, seeds=(100, 101, 102), limit=12):
    """Exhaustive fixed-headcount search; rank mean completions then cycle time.

    All workers are assumed cross-trained and paid equally. Equipment is fixed.
    """
    total = sum(config.staff)
    rows = []
    for a in range(1, min(limit, total-2)+1):
        for b in range(1, min(limit, total-a-1)+1):
            c = total-a-b
            if not 1 <= c <= limit:
                continue
            allocation = (a, b, c)
            runs = replicate(replace(config, staff=allocation), seeds)
            rows.append({"staff": allocation, "mean_completed": mean(x["completed"] for x in runs),
                         "mean_cycle": mean(x["cycle_minutes"] or config.minutes for x in runs)})
    return sorted(rows, key=lambda r: (-r["mean_completed"], r["mean_cycle"], r["staff"]))
