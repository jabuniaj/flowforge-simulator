"""FlowForge warehouse decision laboratory."""
from dataclasses import asdict, replace
from statistics import mean, stdev
from math import ceil
import io
import json
import zipfile
import platform
from importlib.metadata import version
import pandas as pd
import plotly.express as px
import streamlit as st
from flowforge.model import Shift, STATIONS, capacity, replicate, optimize

st.markdown("<style>.block-container{max-width:1250px;padding-top:2rem}h1,h2,h3{letter-spacing:-.035em}[data-testid=stMetric]{border-top:3px solid #0d9488;padding:15px;background:rgba(13,148,136,.06)}</style>",unsafe_allow_html=True)
st.caption("FLOWFORGE / OPERATIONS ENGINEERING LAB")
st.title("Shift Stress Test")
st.write("Test a disruption. Follow the queues. Find a staffing decision you can explain.")
st.caption("Synthetic data • finite-shift SimPy simulation • no claims of measured warehouse performance")

@st.cache_data(show_spinner=False)
def runs(config, seeds):
    return replicate(config,seeds)

@st.cache_data(show_spinner=False)
def search(config):
    return optimize(config)

def summary(results):
    out = {}
    for key in ("completed","unfinished","throughput_per_hour","cycle_minutes","waiting_minutes","labor_cost","cost_per_order"):
        values = [r[key] for r in results if r[key] is not None]
        out[key] = mean(values) if values else None
    return out

def fmt(value):
    return f"{value:,.1f}" if value is not None else "N/A"

METRIC_LABELS = {"completed":"Completed orders", "unfinished":"Unfinished orders",
                 "throughput_per_hour":"Throughput (orders/hour)","cycle_minutes":"Cycle time (min)",
                 "waiting_minutes":"Waiting time (min)","labor_cost":"Labor cost ($)",
                 "cost_per_order":"Labor cost / completion ($)"}

def comparison_table(values):
    return pd.DataFrame(values).rename(index=METRIC_LABELS).round(2)

with st.sidebar:
    st.header("Normal shift")
    hours = st.slider("Shift hours",4,12,8)
    orders = st.number_input("Orders arriving",0,5000,500,25)
    wage = st.number_input("Hourly wage ($)",0.,100.,20.,1.)
    staff = tuple(st.slider(s+" workers",0,12,n) for s,n in zip(STATIONS,(4,3,2)))
    with st.expander("Service and equipment"):
        times = tuple(st.number_input(s+" minutes / order",.1,30.,n,.1) for s,n in zip(STATIONS,(5.,3.,2.)))
        equipment = tuple(st.slider(s+" workstations",0,12,n) for s,n in zip(STATIONS,(12,3,2)))
        cv = st.slider("Processing-time coefficient of variation",0.,1.,.25,.05)
    with st.expander("Reproducibility"):
        seed = st.number_input("First random seed",0,100000,42)
        n_runs = st.slider("Replications",2,20,5)
    st.caption("Cross-trained workers; one worker and workstation per active order. Full-shift wages include idle time.")
base = Shift(orders=int(orders),minutes=hours*60,staff=staff,times=times,equipment=equipment,wage=wage,cv=cv)
scenario = st.selectbox("Disruption",["Normal shift","Demand surge (+40%)","Two packing employees absent","Packing equipment failure","Custom stress test"])
test = base
if scenario == "Demand surge (+40%)":
    test = replace(base,orders=ceil(orders*1.4))
elif scenario == "Two packing employees absent":
    test = replace(base,staff=(staff[0],max(0,staff[1]-2),staff[2]))
elif scenario == "Packing equipment failure":
    test = replace(base,outage_duration=60)
elif scenario == "Custom stress test":
    with st.expander("Disrupted shift controls",expanded=True):
        volume = st.number_input("Disrupted orders",0,10000,int(orders))
        ts = tuple(st.slider(s+" available workers",0,12,n) for s,n in zip(STATIONS,staff))
        tt = tuple(st.number_input(s+" disrupted minutes / order",.1,60.,float(n),.1) for s,n in zip(STATIONS,times))
        te = tuple(st.slider(s+" available workstations",0,12,n) for s,n in zip(STATIONS,equipment))
        station = st.selectbox("Station stopped",STATIONS)
        start = st.slider("Outage starts (minute)",0,hours*60,min(180,hours*60))
        duration = st.slider("Outage duration (minutes)",0,hours*60,60)
        test = replace(base,orders=int(volume),staff=ts,times=tt,equipment=te,outage_station=STATIONS.index(station),outage_start=start,outage_duration=duration)
seeds = tuple(range(int(seed),int(seed)+n_runs))
normal, disrupted = runs(base,seeds), runs(test,seeds)
bs, ds = summary(normal), summary(disrupted)
trace = pd.DataFrame(disrupted[0]["trace"])
tabs = st.tabs(["Shift comparison","Queues & resources","Staffing search","Methods & experiments","Export"])
with tabs[0]:
    cols = st.columns(4)
    for col,key,label in zip(cols,("completed","unfinished","cycle_minutes","cost_per_order"),("Completed orders","Unfinished orders","Cycle time · min","Labor $ / completion")):
        delta = ds[key]-bs[key] if ds[key] is not None and bs[key] is not None else None
        col.metric(label,fmt(ds[key]),fmt(delta) if delta is not None else None,delta_color="normal" if key=="completed" else "inverse")
    st.dataframe(comparison_table({"Normal":bs,"Disrupted":ds}),use_container_width=True)
    paired = [b["completed"]-a["completed"] for a,b in zip(normal,disrupted)]
    st.write(f"Paired completion change: **{mean(paired):+.1f} orders**; replication SD **{stdev(paired):.1f}**, across {n_runs} seeds. SD describes variability, not a confidence interval.")
    chart = pd.DataFrame([{"seed":s,"shift":label,"completed":r["completed"]} for label,rr in (("Normal",normal),("Disrupted",disrupted)) for s,r in zip(seeds,rr)])
    st.plotly_chart(px.bar(chart,x="seed",y="completed",color="shift",barmode="group",color_discrete_sequence=["#0d9488","#e58a32"]),use_container_width=True)
    cap = capacity(test)
    st.subheader("Capacity reference")
    st.write("Tightest theoretical station(s): **"+", ".join(cap["bottlenecks"])+"**")
    st.dataframe(pd.DataFrame([cap["capacity"]],index=["Nominal orders / shift"]),use_container_width=True)
    st.caption("Mean-time capacity is a planning reference, not a strict stochastic upper bound. Ties use unrounded capacities. Pipeline fill and arrival timing affect finite-shift output.")
    evidence = pd.DataFrame(disrupted[0]["stations"])
    largest = evidence.loc[evidence.average_queue.idxmax()]
    st.info(f"In seed {seeds[0]}, {largest['station']} had the largest time-average queue ({largest['average_queue']:.1f} orders). Inspect resource utilization to distinguish workload pressure from equipment constraints. Improving one station can move queues downstream.")
with tabs[1]:
    st.caption(f"Detailed trace: seed {seeds[0]}. Summary metrics average all replications.")
    details = pd.DataFrame(disrupted[0]["stations"])
    st.dataframe(details,use_container_width=True)
    st.plotly_chart(px.line(trace,x="minute",y=list(STATIONS),labels={"value":"Queued orders","variable":"Station"}),use_container_width=True)
    util = details.melt(id_vars="station",value_vars=["worker_utilization","workstation_utilization"],var_name="resource",value_name="utilization")
    fig = px.bar(util,x="station",y="utilization",color="resource",barmode="group")
    fig.update_yaxes(tickformat=".0%",range=[0,1])
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Utilization = productive processing / installed resource minutes. Downtime reduces productive utilization. Queues exclude in-service orders. Cycle and waiting averages include completed orders only; delayed unfinished orders are excluded.")
with tabs[2]:
    st.subheader("Redistribute the available workforce")
    st.write("Exhaustive integer search: same headcount and wage, 1–12 workers per station, fixed equipment. Rank mean completions first, then mean cycle time. Train on seeds 100–102; validate on separate seeds 200–209.")
    if sum(test.staff)<3:
        st.warning("At least three available workers are required for one worker per station.")
    elif st.button("Evaluate staffing allocations",type="primary"):
        with st.spinner("Evaluating allocations…"):
            candidates = search(test)
            improved = replace(test,staff=candidates[0]["staff"])
            validation_seeds = tuple(range(200,210))
            before,after = runs(test,validation_seeds),runs(improved,validation_seeds)
        st.write(f"Selected picking / packing / shipping: **{' / '.join(map(str,improved.staff))}**")
        change = mean(b["completed"]-a["completed"] for a,b in zip(before,after))
        st.write(f"Held-out paired change: **{change:+.1f} completions**. Full-shift labor budget: **${sum(test.staff)*hours*wage:,.2f}** for both allocations.")
        if change<=0:
            st.warning("No held-out mean throughput improvement. Retain the current allocation or investigate more replications.")
        else:
            st.success("Held-out mean throughput improved in this synthetic experiment. Verify cross-training and equipment assumptions before recommending an operational change.")
        st.dataframe(comparison_table({"Current":summary(before),"Selected":summary(after)}),use_container_width=True)
        table = pd.DataFrame(candidates)
        st.dataframe(table,use_container_width=True)
        st.download_button("Download staffing search CSV",table.to_csv(index=False),"staffing_search.csv","text/csv")
        st.download_button("Download staffing validation JSON",json.dumps({"config":asdict(test),"selected":asdict(improved),"training_seeds":[100,101,102],"validation_seeds":validation_seeds,"before":before,"after":after},allow_nan=False),"staffing_validation.json","application/json")
with tabs[3]:
    st.markdown('''### Model contract
Orders arrive uniformly across the shift conditional on a fixed count, then visit picking → packing → shipping. Gamma service times use the entered mean and coefficient of variation (zero means deterministic). FCFS station pools limit simultaneous work to min(workers, workstations). A full-station outage pauses active work and resumes without losing progress; workers remain reserved.

The shift starts empty and stops without overtime or drain-down. Available workers receive full-shift wages, including idle time. Absent workers are excluded from labor cost. No benefits, equipment cost, inventory shortages, travel, breaks, batching, rework, skill differences or downstream blocking are modeled.

### Three experiments to reproduce
1. **Demand surge:** select +40% demand. Compare unfinished orders, queues and throughput. Investigate whether extra arrivals produce backlog without proportional output.
2. **Employee shortage:** remove two packing workers, then run staffing search at reduced headcount. Investigate whether redistribution helps under equipment limits.
3. **Equipment downtime:** stop packing at minute 180 for 60 minutes; vary timing and duration. Investigate how queues persist after recovery.

These are hypotheses, not measured facility findings. Download actual results for your settings. The repository case study records the default experiments.

### Add your engineering judgment
Record why you chose a scenario, which result surprised you, which assumption you would measure first, and whether moving workers is practical. Describe simulated gains as simulated gains.
''')
with tabs[4]:
    report = {"model_version":"0.2.0","environment":{"python":platform.python_version(),"platform":platform.system(),"simpy":version("simpy"),"streamlit":version("streamlit")},"data":"synthetic","seeds":seeds,"baseline_config":asdict(base),"stress_config":asdict(test),"baseline":normal,"stress":disrupted}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("experiment.json",json.dumps(report,indent=2,allow_nan=False))
        z.writestr("summary.csv",pd.DataFrame({"Normal":bs,"Disrupted":ds}).to_csv())
        z.writestr("stress_orders_first_seed.csv",pd.DataFrame(disrupted[0]["orders"]).to_csv(index=False))
        z.writestr("stress_queues_first_seed.csv",trace.to_csv(index=False))
    st.download_button("Download reproducible experiment ZIP",buffer.getvalue(),"flowforge_experiment.zip","application/zip")
    st.caption("Configurations, seeds, per-run results, completed-order records and queue trace. No real customer data.")
