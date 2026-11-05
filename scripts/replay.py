"""Replay a downloaded experiment ZIP or extracted experiment.json."""
import argparse
import json
import zipfile
from math import isclose
from flowforge.model import Shift, replicate


def equivalent(a, b):
    """Require exact counts/structure; tolerate cross-platform float rounding."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a, float) and isinstance(b, (float,int)):
        return isclose(a,b,rel_tol=1e-10,abs_tol=1e-8)
    return a == b


def replay(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            report = json.loads(z.read("experiment.json"))
    else:
        with open(path,encoding="utf-8") as f:
            report = json.load(f)
    output = {}
    for label, key in (("baseline","baseline_config"),("stress","stress_config")):
        values = report[key].copy()
        for field in ("staff","times","equipment"):
            values[field] = tuple(values[field])
        results = replicate(Shift(**values),report["seeds"])
        expected = report[label]
        output[label] = {"completed":[r["completed"] for r in results],
                         "matches_export":equivalent(results,expected),
                         "bitwise_equal":results == expected}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    print(json.dumps(replay(parser.parse_args().report),indent=2))
