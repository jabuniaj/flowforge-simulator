from dataclasses import asdict
import json
import zipfile
from flowforge.model import Shift, replicate
from scripts.replay import replay, equivalent


def test_export_replay(tmp_path):
    config = Shift(orders=5)
    seeds = [1,2]
    results = replicate(config,seeds)
    report = {"baseline_config":asdict(config),"stress_config":asdict(config),
              "seeds":seeds,"baseline":results,"stress":results}
    path = tmp_path / "experiment.zip"
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("experiment.json",json.dumps(report))
    assert all(r["matches_export"] for r in replay(path).values())


def test_float_tolerance_does_not_hide_changed_counts():
    assert equivalent({"completed":5,"time":1.0},{"completed":5,"time":1.0+1e-12})
    assert not equivalent({"completed":5},{"completed":6})
