# FlowForge — Warehouse & Factory Optimization Simulator

An engineering portfolio project for testing warehouse staffing decisions under disruption. The current scope is a warehouse order-fulfillment line; factory routing is future work.

**[Open the live Shift Stress Test](https://flowforge-simulator-uyfsb446fp5yi7yw5q2cdw.streamlit.app/)**

FlowForge follows orders through picking, packing and shipping with a SimPy discrete-event simulation. It compares a normal shift against demand surges, absences, equipment downtime or custom settings. All inputs are **synthetic assumptions**, not measurements from a real facility.

## What works

- FCFS queues, stochastic service times, finite shifts, workstation constraints and pause/resume outages.
- Multiple reproducible runs, paired comparisons and queue/utilization charts.
- Exhaustive staffing search at fixed headcount and wage; separate seeds for validation.
- All tied nominal capacity bottlenecks are reported, including the 5/3/2 staffing example with 480 orders per station.
- ZIP reports with configuration, seeds, summaries, individual runs and first-run order/queue records; CSV and JSON staffing reports.
- Automated model and Streamlit interaction tests, plus GitHub Actions.

## Run locally

Python 3.11 or 3.12 recommended. From the repository root:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m streamlit run app.py
python -m pytest -q
python -m scripts.experiments
```

The experiment script rewrites `docs/experiment_results.json`. Production needs only `requirements.txt`. The tested direct dependency versions are recorded in `requirements-tested.txt`; use that file to reproduce this release's environment.

## Engineering method

Station capacity remains a **mean-time reference**, separate from simulation. Each order is an event process requesting a limited station resource. Active capacity is min(workers, workstations). The search enumerates feasible integer allocations and ranks mean completed orders first, then completed-order cycle time. It does not claim a globally optimal real-world staffing plan.

Read the [technical case study](docs/CASE_STUDY.md), [model contract](docs/MODEL.md), and [recorded synthetic experiments](docs/experiment_results.json). The case study includes interview questions and space for the student's own decisions and observations.

## Repository

```text
app.py                     Streamlit dashboard and exports
flowforge/model.py         Input validation, capacity, simulation and search
tests/                     Model invariants and app interactions
scripts/experiments.py      Reproducible experiment runner
docs/                      Methods, results and case study
.github/workflows/tests.yml Continuous testing
```

## Limits and next steps

Starts empty; stops at shift end without clearing work in progress. No breaks, travel, inventory, batching, rework, overtime, skill differences or finite downstream buffers. Workers are assumed cross-trained and paid equally. Cycle and waiting averages include **completed orders only**. This selection effect matters in overloaded shifts.

CSV input and calibration against observed warehouse data are not implemented. Next steps are arrival/service-data import with validation, skill and break constraints, and sensitivity analysis over arrival patterns. Before adding complexity, compare model behavior with measured process observations.

Development assistance was used for implementation and documentation. No personal fieldwork, independent authorship or real operational savings are asserted. The student should review, modify and explain the model before presenting it.
