# FlowForge: what happens when a shift goes wrong?

## Problem and project motivation

A staffing plan that seems adequate from average processing times can still leave orders unfinished. Orders arrive over time, stations compete for limited resources, and a disruption can move the queue elsewhere. FlowForge studies those interactions in a small, inspectable warehouse model.

This project was selected as an engineering portfolio exercise connecting process analysis, simulation and constrained decisions. It does not claim access to a real warehouse. **Student contribution to add:** why this problem interests you, the alternatives you considered, and the decisions you personally reviewed or changed.

## From capacity estimate to simulation

The original prototype divided worker minutes by processing time. Its bottleneck calculation returned only the first minimum, so equal 480-order station capacities were reported as one bottleneck. The revised capacity reference reports every tie. More importantly, it is separated from the discrete-event model: even equal nominal capacities do not guarantee 480 completions because the shift starts empty, arrivals are spread through time, and the last order needs time at all three stations.

SimPy order processes pass through FCFS picking, packing and shipping pools. Processing varies randomly; outages pause work. Queue area is integrated at state changes and productive resource time is clipped at shift close. See [MODEL.md](MODEL.md) for exact definitions and limitations.

## Recorded experiments

The following are **synthetic simulation results**, not measured productivity gains. Defaults: 8 hours, 500 orders, 4/3/2 workers, 12/3/2 workstations, 5/3/2 minute service means, CV 0.25, $20/hour. Search uses seeds 100–102; the table averages validation seeds 200–209. Run `python -m scripts.experiments` to regenerate the checked-in JSON.

| Experiment | Current workers | Selected workers | Current completions | Selected completions | Current cycle min | Selected cycle min |
|---|---|---|---:|---:|---:|---:|
| Normal | 4/3/2 | 4/3/2 | 376.1 | 376.1 | 65.5 | 65.5 |
| +40% demand (700 orders) | 4/3/2 | 4/3/2 | 377.5 | 377.5 | 117.7 | 117.7 |
| Two packing absences | 4/1/2 | 3/2/2 | 156.6 | 283.2 | 171.5 | 110.6 |
| Packing stopped minutes 180–240 | 4/3/2 | 4/3/2 | 370.7 | 370.7 | 86.3 | 86.3 |

### Demand surge

Increasing arrivals by 200 raised mean completions by only 1.4 in these runs; mean unfinished work rose from 123.9 to 322.5. The existing workforce was already constrained upstream. Same-headcount search retained 4/3/2. This experiment supports investigating capacity or demand scheduling, rather than assuming redistribution can absorb any surge.

### Employee shortage

Two packing absences reduce the workforce from nine to seven. At that reduced headcount, moving one picker to packing changed mean completions from 156.6 to 283.2 on the separate validation seeds. Both shortage allocations cost $1,120 per shift. Mean cost per completion changed from $7.15 to $3.96. The selected allocation still leaves 216.8 orders unfinished: it mitigates the shortage, rather than recovering normal output. Its picking reference capacity becomes 288 orders; the bottleneck moves upstream.

This is a simulated comparison under perfect cross-training. A real transfer could require training, walking, supervision or a different wage. Those costs are absent.

### Equipment downtime

One hour of packing downtime reduced mean completions from 376.1 to 370.7, much less than nominal packing capacity lost. Picking feeds the line more slowly, so packing can recover some backlog after repair. Mean completed-order cycle time still rose from 65.5 to 86.3 minutes. Looking only at throughput would miss that delay. The search retained current staffing; adding workers cannot repair a workstation constraint by itself.

## Verification and lessons

Automated tests cover the 480/480/480 tie, zero orders, zero staff, full-shift outage, single-order deterministic service, pause/resume timing, utilization accounting, horizon censoring, equipment limits, reproducibility, invalid inputs, search constraints and Streamlit scenario/search execution. GitHub Actions runs these checks on pushes and pull requests. Tests verify the implementation against its contract; they do not establish real-world validity.

The most useful lesson from these runs is that a recommendation can be to keep the current allocation. A staffing algorithm should expose the limits of a decision, including remaining backlog and assumptions, rather than always claim an improvement.

## Limitations and next work

The model starts empty and lacks travel, breaks, inventory, rework, batching, finite downstream buffers and skill differences. Mean cycle time excludes unfinished orders, which can bias interpretation in overloaded scenarios. Fixed synthetic demand and uniform arrivals do not capture a real order profile. More replications and sensitivity analysis are needed before comparing small differences.

CSV upload/calibration, observed arrival distributions, a skill matrix, worker breaks, overtime decisions, dynamic single-machine outages and factory routes remain future work. A useful next validation exercise is one measured station observed for a short interval, with permission, followed by a comparison of queue and service-time distributions.

## Demonstrating and defending the project

Be ready to explain:

1. Why station capacity and finite-shift throughput differ.
2. How a SimPy resource queues an order and releases the next one.
3. Why the same random seeds and separate validation seeds are used.
4. The search objective, integer constraints and cross-training assumption.
5. Why completed-order cycle time can hide unfinished work.
6. Why the packing outage can increase delay more than it reduces throughput.
7. Which assumptions you would measure first before recommending a real staffing change.

**Student notes to complete:** What surprised you? Which part did you inspect or modify? What failed during your own experiments? What would you simplify or change? Be explicit about development assistance and your own work; do not imply fieldwork or authorship you cannot support.
