# Model contract, version 0.2.0

## Inputs and units

Minutes are the internal unit. Default shift: 480 minutes; 500 orders; workers 4/3/2; service means 5/3/2 minutes; installed workstations 12/3/2; wage $20/hour; coefficient of variation 0.25. These values are illustrative synthetic assumptions chosen to create capacity pressure, not industry benchmarks. Workstations at picking represent concurrent work positions, not a claim about physical layout.

Orders arrive at sorted uniform random times conditional on the requested count. This is not a Poisson process with a random count. Gamma service durations have shape 1/CV² and scale mean×CV². CV=0 gives deterministic times. There is no receiving/inventory replenishment process; order arrival is the entry boundary.

At each station, a pooled FCFS resource has min(workers, workstations) slots. One occupied slot needs one worker and one workstation. Zero slots leave arriving work queued. A full-station outage pauses processing, retaining workers, and resumes remaining work at recovery. Partial availability is represented by a lower workstation count for the entire shift. There is no dynamic single-machine failure model.

All events at or before shift end execute; later work is censored. No warm-up deletion is appropriate for the intended empty-start shift experiment. The model does not represent a steady-state facility.

## Measurements

- Throughput: completed orders / shift hours.
- Unfinished: released orders minus completions, including queued, processing and paused work.
- Cycle: completion minus arrival, averaged over completed orders.
- Waiting: station queue delays plus outage pauses, averaged over completed orders.
- Station average wait: queue delay among orders that started service at that station; excludes outage pauses. This population differs from completed-order waiting time.
- Time-average queue: exact area under the waiting-order count / shift minutes. The displayed trace samples every five minutes; it is not used to calculate the average.
- Peak queue: maximum observed request queue count, including transient requests before immediate grants.
- Productive worker utilization: processing minutes / (workers × shift minutes). Workstation utilization uses installed workstations in the denominator. Both exclude paused processing and include only work before close.
- Cost/order: full-shift wages / completed orders; undefined with no completions. Costs exclude absent staff, benefits, equipment and overtime.

The capacity calculator uses floor(min(staff, equipment) × available minutes / mean service time). It identifies all ties using the unrounded capacities with numerical tolerance. This is not a finite-shift completion forecast or a strict stochastic upper bound. The legacy output key `completed_upper_bound` denotes the nominal deterministic bound only.

## Randomness and comparisons

Arrival streams use a seeded Python Random instance. Service streams are keyed to seed, order and station, so reallocating workers does not consume random numbers in a different event order. Different demand counts change sorted arrival times; demand comparisons share randomness but do not preserve each order's arrival timestamp. Results are repeatable for the same model, Python environment, inputs and seeds.

The UI shows replication means and the sample standard deviation of paired completion differences. It does not display a confidence interval or claim statistical significance. Per-run labor cost/order is averaged across runs with at least one completion; inspect individual runs for zero-completion cases.

## Staffing search

Enumerate all (p,k,s) integers with p+k+s equal to available headcount and 1≤p,k,s≤12. Wage and workstation counts remain fixed. Rank mean completions across seeds 100–102, breaking ties by mean completed-order cycle time, then allocation tuple for deterministic ordering. A no-completion run receives shift length as its cycle-time ranking penalty. Evaluate selected and current allocations on paired seeds 200–209. Selection bias and uncertainty remain; three training seeds are a computational compromise, not a proof of optimal expected output.

The search assumes full cross-training, equal worker productivity and no transfer cost. It optimizes initial shift allocation, not mid-shift reassignment. No OR-Tools dependency is needed for this small exhaustive search.

## References

- [SimPy shared resources](https://simpy.readthedocs.io/en/stable/simpy_intro/shared_resources.html): process requests and FIFO resource queues.
- [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest): app interaction verification.

These references describe software behavior; they do not validate the synthetic warehouse assumptions.
