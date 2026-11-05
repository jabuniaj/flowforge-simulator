"""Run from repo root: python -m scripts.experiments."""
from dataclasses import replace, asdict
from pathlib import Path
from statistics import mean
import json
from flowforge.model import Shift, replicate, optimize


def run():
    base = Shift()
    scenarios = {"normal":base,"demand_surge":replace(base,orders=700),
                 "employee_shortage":replace(base,staff=(4,1,2)),
                 "equipment_downtime":replace(base,outage_duration=60)}
    output = {}
    for name,config in scenarios.items():
        best = optimize(config)[0]["staff"]
        selected = replace(config,staff=best)
        seeds = tuple(range(200,210))
        before,after = replicate(config,seeds),replicate(selected,seeds)
        keys = ("completed","unfinished","cycle_minutes","waiting_minutes","cost_per_order")
        output[name] = {"config":asdict(config),"selected":asdict(selected),"seeds":seeds,
                        "before":{k:mean(r[k] for r in before if r[k] is not None) for k in keys},
                        "after":{k:mean(r[k] for r in after if r[k] is not None) for k in keys}}
    Path("docs").mkdir(exist_ok=True)
    Path("docs/experiment_results.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps(output,indent=2))


if __name__ == "__main__":
    run()
