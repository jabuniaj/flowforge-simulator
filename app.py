"""FlowForge — learn operations by rescuing a simulated warehouse shift."""
from dataclasses import asdict
from pathlib import Path
from statistics import mean
import json
import runpy
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from flowforge.challenges import MISSIONS, SEEDS, build_plan, evaluate
from flowforge.model import STATIONS, capacity
from flowforge.replay_view import replay_html

st.set_page_config(page_title="FlowForge | Rescue the shift",page_icon="📦",layout="wide")
st.markdown('''<style>
.block-container{max-width:1180px;padding-top:2.4rem}h1,h2,h3{letter-spacing:-.035em}h1{font-size:3.2rem!important;line-height:1.05!important}.eyebrow{font-size:11px;letter-spacing:2.4px;color:#0d8477;font-weight:800;margin-bottom:16px}.lead{font-size:19px;color:#536b77;max-width:760px;line-height:1.6}.brief{background:#122c3a;border-radius:18px;padding:28px 30px;color:#e5edf0;margin:24px 0}.brief p{color:#c5d7df;line-height:1.7;font-size:16px}.brief h2{color:white;margin:7px 0 12px}.goal{border-left:3px solid #55d1b8;padding:10px 16px;background:#203e4c;border-radius:0 8px 8px 0;color:white;font-weight:600}.step{font-size:12px;letter-spacing:1.5px;color:#0d8477;font-weight:800;margin:15px 0}.role{border:1px solid #dce5e8;border-radius:12px;padding:18px;min-height:125px;background:white}.role strong{display:block;font-size:17px;margin-bottom:8px}.role span{font-size:14px;color:#526c79}[data-testid=stMetric]{background:#f0f5f5;border-radius:12px;padding:16px}[data-testid=stMetricLabel]{font-size:13px}.stButton>button{border-radius:9px;font-weight:650}div[data-testid=stAlert]{border-radius:12px}div[data-testid=stTabs] button{font-weight:650}@media(max-width:640px){h1{font-size:2.25rem!important}.brief{padding:22px}.lead{font-size:17px}.role{min-height:100px}button{min-height:44px!important}}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def test_plan(mid,staff,bench=False,repair=False):
    return evaluate(MISSIONS[mid],staff,bench,repair)

if "history" not in st.session_state:
    st.session_state.history = {m.id:[] for m in MISSIONS}
with st.sidebar:
    st.markdown("### 📦 FlowForge")
    st.caption("LEARN BY RUNNING THE SHIFT")
    section = st.radio("Explore",["Challenge room","Free simulator","How to play"],label_visibility="collapsed",key="section")
    st.divider()
    passed = sum(any(h['successes']>=8 for h in st.session_state.history[m.id]) for m in MISSIONS)
    progress_text = st.empty()
    progress_text.markdown(f"**{passed} / {len(MISSIONS)} missions solved**")
    mission_progress = st.progress(passed/len(MISSIONS))
    for m in MISSIONS:
        done = any(h['successes']>=8 for h in st.session_state.history[m.id])
        st.caption(('✓ ' if done else '○ ')+m.title)
    st.caption("Progress stays in this browser session. Download your notebook to keep your experiments.")
    st.divider()
    st.caption("A synthetic learning environment. Decisions affect simulated orders, not a real warehouse.")

if section == "Free simulator":
    runpy.run_path(str(Path(__file__).with_name("workbench.py")),run_name="__main__")
    st.stop()
if section == "How to play":
    st.title("A decision. A test. A lesson.")
    st.write("You run a small warehouse for one shift. Customer orders pass through three steps:")
    for name,description in zip(STATIONS,("Find and collect the items.","Box the items and prepare the parcel.","Label and hand off the parcel for dispatch.")):
        st.subheader(name)
        st.write(description)
    st.markdown('''1. **Read the situation.** Each mission has a delivery target and a fixed team.
2. **Build a plan.** Move workers, rent a bench or shorten a repair when the mission allows it.
3. **Predict the result.** Make a small prediction before seeing the answer.
4. **Run the shift.** The simulator tests the same plan across ten random shifts.
5. **Watch the queue.** Scrub the replay to see where work accumulates.
6. **Try another decision.** Keep an experiment notebook and explain your result.

You solve a mission when at least eight of the ten simulated shifts reach its target within the budget. This is a teaching rule, not a guarantee about real operations.
''')
    with st.expander("What does the model assume?"):
        st.write("Orders arrive throughout the shift. Each order needs one worker and one workstation at every station. Workers are equally skilled and cross-trained. Task times vary; the shift starts empty and ends without overtime. No breaks, travel, rework or inventory shortages are included. Equipment and repair prices are invented teaching inputs. The Free simulator contains the full model details and exports.")
    st.stop()

st.markdown('<div class="eyebrow">FLOWFORGE / THE SHIFT CHALLENGES</div>',unsafe_allow_html=True)
st.title("Can you rescue the shift?")
st.markdown('<p class="lead">A queue is growing. The truck will not wait. Make one decision, run the warehouse, and see what your plan actually changes.</p>',unsafe_allow_html=True)
mid = st.radio("Choose your mission",range(len(MISSIONS)),format_func=lambda i:f"0{i+1} · {MISSIONS[i].title}",horizontal=True,key="mission")
m = MISSIONS[mid]
base = test_plan(mid,m.config.staff)
st.markdown(f'<div class="brief"><div class="eyebrow" style="color:#7dd3c4">{m.subtitle}</div><h2>{m.title}</h2><p>{m.brief}</p><div class="goal">YOUR MISSION · {m.goal}</div></div>',unsafe_allow_html=True)
cols = st.columns(4)
cols[0].metric("Orders arriving",m.config.orders)
cols[1].metric("People on your team",sum(m.config.staff))
cols[2].metric("Shift length",f"{m.config.minutes/60:g} hours")
cols[3].metric("Extra spending allowed",f"${m.budget}")
st.caption(f"If you change nothing: about {base['baseline_mean']:.0f} orders finish and {m.config.orders-base['baseline_mean']:.0f} remain. This forecast averages the same 10 synthetic shifts used to test your plan.")

st.markdown('<div class="step">01 / BUILD YOUR PLAN</div>',unsafe_allow_html=True)
st.write("Keep the same team. Choose where each person works.")
cols = st.columns(3)
roles = ("Collect items from storage.","Box items at an available bench.","Prepare parcels for dispatch.")
allocation = []
for i,(col,s) in enumerate(zip(cols,STATIONS)):
    with col:
        st.markdown(f'<div class="role"><strong>{s}</strong><span>{roles[i]}<br>Typical task: {m.config.times[i]:g} min / order<br>Working positions: {m.config.equipment[i]}</span></div>',unsafe_allow_html=True)
        allocation.append(st.number_input(s+" team",0,12,m.config.staff[i],1,key=m.id+f"_staff{i}"))
staff = tuple(allocation)
remaining = sum(m.config.staff)-sum(staff)
if remaining>0:
    st.warning(f"You still have {remaining} {'person' if remaining==1 else 'people'} to assign.")
elif remaining<0:
    st.warning(f"You assigned {-remaining} more people than your team has. Move them from another station.")
else:
    st.caption("✓ Everyone is assigned. You can move people again after testing.")
bench = repair = False
if m.bench_cost or m.repair_cost:
    st.write("**Choose an intervention**")
    a,b = st.columns(2)
    if m.bench_cost:
        bench = a.checkbox(f"Rent one packing bench · ${m.bench_cost}",key=m.id+"_bench",help="Adds one working position while packing is running. It does not shorten a station-wide outage.")
    if m.repair_cost:
        repair = b.checkbox(f"Repair crew · ${m.repair_cost}",key=m.id+"_repair",help=f"Cuts the packing stop from {m.config.outage_duration:g} to {m.repaired_duration:g} minutes.")
cost = int(bench)*m.bench_cost+int(repair)*m.repair_cost
valid = True
try:
    build_plan(m,staff,bench,repair)
except ValueError as exc:
    valid = False
    if remaining==0:
        st.warning(str(exc))
if m.budget:
    st.caption(f"Extra spending: ${cost} / ${m.budget}. Existing shift wages are unchanged by reassignment.")

st.markdown('<div class="step">02 / MAKE A PREDICTION</div>',unsafe_allow_html=True)
prediction = st.radio("Compared with changing nothing, my plan will finish…",["More orders","About the same (within 5 orders)","Fewer orders"],horizontal=True,key=m.id+"_prediction")
note = st.text_input("Why do you think so?",placeholder="Example: the packers are receiving work faster than they can box it…",key=m.id+"_reason")
run, hint = st.columns([2,3])
clicked = run.button("Run my shift →",type="primary",disabled=not valid,use_container_width=True)
with hint:
    if st.button("Give me a hint",key=m.id+"_hint_button"):
        st.session_state[m.id+"_hint"] = True
if st.session_state.get(m.id+"_hint"):
    st.info(m.hint)
if clicked:
    with st.spinner("Running your plan through ten simulated shifts…"):
        result = test_plan(mid,staff,bench,repair)
    attempt = {"attempt":len(st.session_state.history[m.id])+1,"staff":staff,"bench":bench,"repair":repair,
        "extra_cost":cost,"mean_completed":round(result['plan_mean'],1),"successes":result['successes'],
        "prediction":prediction,"reason":note}
    st.session_state.history[m.id].append(attempt)
    st.session_state[m.id+"_result"] = result
    st.session_state[m.id+"_attempt"] = attempt
    passed = sum(any(h['successes']>=8 for h in st.session_state.history[item.id]) for item in MISSIONS)
    progress_text.markdown(f"**{passed} / {len(MISSIONS)} missions solved**")
    mission_progress.progress(passed/len(MISSIONS))

result = st.session_state.get(m.id+"_result")
if result:
    attempt = st.session_state[m.id+"_attempt"]
    st.divider()
    st.markdown('<div class="step">03 / THE REVEAL</div>',unsafe_allow_html=True)
    if (staff,bench,repair)!=(tuple(attempt['staff']),attempt['bench'],attempt['repair']):
        st.info("You have changed the controls. These results show your last tested plan; run again to test the new one.")
    if result['successes']>=8:
        st.success(f"Mission solved. Your plan reached the target in {result['successes']} of 10 shifts.")
    else:
        st.warning(f"Not there yet: {result['successes']} of 10 shifts reached the target. Change one decision and try again.")
    st.write(f"**Tested team:** {attempt['staff'][0]} picking → {attempt['staff'][1]} packing → {attempt['staff'][2]} shipping. Extra spending: **${attempt['extra_cost']}**.")
    a,b,c = st.columns(3)
    a.metric("Orders completed · average",f"{result['plan_mean']:.0f}",f"{result['gain']:+.0f} vs doing nothing")
    b.metric("Orders still unfinished",f"{m.config.orders-result['plan_mean']:.0f}")
    c.metric("Shifts reaching your goal",f"{result['successes']} / 10")
    actual = "More orders" if result['gain']>5 else "Fewer orders" if result['gain']< -5 else "About the same (within 5 orders)"
    st.write(f"**Your prediction:** {attempt['prediction']}. **What happened:** {actual.lower()}.")
    if attempt['reason']:
        st.caption("Your explanation: "+attempt['reason'])
    if result['gain']<=5 and staff!=m.config.staff:
        st.write("A different allocation is not automatically a better one. Look at both worker coverage and working positions before moving another person.")
    st.write(m.lesson)
    view, evidence, notebook = st.tabs(["Watch the shift","Why did this happen?","My experiment notebook"])
    with view:
        chosen = st.radio("Replay",["My plan","Change nothing"],horizontal=True,key=m.id+"_replay")
        index = st.select_slider("Choose a simulated run",options=list(range(1,11)),value=1,key=m.id+"_run")-1
        selected = result['after' if chosen=="My plan" else 'before'][index]
        components.html(replay_html(selected,chosen,m.target),height=370,scrolling=False)
        st.caption(f"At shift close: {selected['completed']} completed, {selected['unfinished']} unfinished. The final playback snapshot is taken just before close.")
    with evidence:
        names = list(STATIONS)
        after_q = [mean(r['stations'][i]['average_queue'] for r in result['after']) for i in range(3)]
        chart = pd.DataFrame({'Station':names*2,'Average orders waiting':result['queue_means']+after_q,'Plan':['Change nothing']*3+['My plan']*3})
        st.plotly_chart(px.bar(chart,x='Station',y='Average orders waiting',color='Plan',barmode='group',color_discrete_sequence=['#9aaeb8','#0d9488']),use_container_width=True)
        st.write("The tallest bar shows where orders spent the most time waiting. It is evidence of queue pressure, not proof that adding a worker there will help. Check whether equipment or downtime prevents that worker from doing useful work.")
        cap = capacity(result['config'])
        st.caption("Mean-time capacity reference for your plan: "+' · '.join(f"{s} {n}" for s,n in cap['capacity'].items())+" orders. This reference does not predict the exact number completed.")
        totals = pd.DataFrame({'Run':range(1,11),'Change nothing':[r['completed'] for r in result['before']],'My plan':[r['completed'] for r in result['after']]})
        st.dataframe(totals,hide_index=True,use_container_width=True)
        st.caption("Both plans use the same arrival and service random inputs. Ten successful runs are ten observations, not a 100% real-world guarantee.")
        if st.button("Reveal a working reference plan",key=m.id+"_reference_button"):
            st.session_state[m.id+"_reference"] = True
        if st.session_state.get(m.id+"_reference"):
            ref = test_plan(mid,m.reference_staff,m.reference_bench,m.reference_repair)
            changes = [' / '.join(map(str,m.reference_staff))+' workers (picking / packing / shipping)']
            if m.reference_bench: changes.append('rent one bench')
            if m.reference_repair: changes.append('use the repair crew')
            st.info('Reference: '+', '.join(changes)+f". It completes {ref['plan_mean']:.1f} orders on average and reaches the target in {ref['successes']}/10 runs. This is a tested teaching example, not a claim of optimality.")
    with notebook:
        history = st.session_state.history[m.id]
        st.dataframe(pd.DataFrame(history),hide_index=True,use_container_width=True)
        reflection = st.text_area("What changed your mind? What will you try next?",key=m.id+"_reflection")
        report = {'mission':m.id,'model_version':'0.3.0','synthetic':True,'seeds':SEEDS,'mission_config':asdict(m.config),'tested_config':asdict(result['config']),'history':history,'reflection':reflection,'baseline':result['before'],'tested':result['after']}
        st.download_button("Save my experiment notebook",json.dumps(report,indent=2),f"flowforge_{m.id}_notebook.json","application/json")
else:
    st.caption("Your prediction and result will appear here after your first run. Change one thing at a time to learn what caused the difference.")
