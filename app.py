"""FlowForge | Warehouse stress-test prototype.

Version 0.1 estimates theoretical station capacity.
It is not yet a discrete-event simulation.
"""
import csv
import io
from math import floor, ceil

import streamlit as st

st.set_page_config(page_title="FlowForge", page_icon="📦", layout="wide")

st.markdown(
    "<style>.block-container{max-width:1120px;padding-top:2rem}"
    "h1,h2,h3{letter-spacing:-.03em}</style>",
    unsafe_allow_html=True,
)
st.caption("FLOWFORGE  /  ENGINEERING LAB 01")
st.title("What happens when a shift goes wrong?")
st.write(
    "A warehouse stress test for thinking through staffing, bottlenecks, "
    "and the cost of operational surprises."
)


def estimate(orders, shift_hours, staff, times, wage, shipping_outage=0):
    """Calculate theoretical orders-per-shift capacity at each station."""
    minutes = shift_hours * 60
    capacity = {
        "Picking": floor(staff["Picking"] * minutes / times["Picking"]),
        "Packing": floor(staff["Packing"] * minutes / times["Packing"]),
        "Shipping": floor(
            staff["Shipping"] * max(0, minutes - shipping_outage)
            / times["Shipping"]
        ),
    }
    completed = min(orders, *capacity.values())
    labor_cost = sum(staff.values()) * shift_hours * wage
    return {
        "orders": orders,
        "capacity": capacity,
        "completed": completed,
        "unfinished": orders - completed,
        "bottleneck": min(capacity, key=capacity.get),
        "labor_cost": labor_cost,
        "cost_per_order": labor_cost / completed if completed else None,
    }


with st.sidebar:
    st.header("Set up a shift")
    shift_hours = st.slider("Shift hours", 4, 12, 8)
    orders = st.number_input("Orders arriving", min_value=1, max_value=5000, value=500, step=25)
    wage = st.number_input("Hourly wage ($)", 10.0, 60.0, 20.0, step=1.0)
    st.subheader("Workers")
    staff = {
        "Picking": st.slider("Picking workers", 1, 12, 4),
        "Packing": st.slider("Packing workers", 1, 12, 3),
        "Shipping": st.slider("Shipping workers", 1, 12, 2),
    }
    with st.expander("Minutes per order"):
        times = {
            "Picking": st.number_input("Picking time", 0.5, 30.0, 5.0, step=0.5),
            "Packing": st.number_input("Packing time", 0.5, 30.0, 3.0, step=0.5),
            "Shipping": st.number_input("Shipping time", 0.5, 30.0, 2.0, step=0.5),
        }

st.subheader("Shift stress test")
scenario = st.radio(
    "What goes wrong?",
    [
        "Nothing — normal shift",
        "Orders spike by 30%",
        "One packing worker calls out",
        "Shipping stops for 45 minutes",
    ],
    horizontal=True,
)

baseline = estimate(orders, shift_hours, staff, times, wage)
test_staff = staff.copy()
test_orders = orders
outage = 0
if scenario == "Orders spike by 30%":
    test_orders = ceil(orders * 1.3)
elif scenario == "One packing worker calls out":
    test_staff["Packing"] = max(0, test_staff["Packing"] - 1)
elif scenario == "Shipping stops for 45 minutes":
    outage = 45
result = estimate(test_orders, shift_hours, test_staff, times, wage, outage)

a, b, c, d = st.columns(4)
a.metric("Completed orders", result["completed"],
         delta=result["completed"] - baseline["completed"])
b.metric("Unfinished orders", result["unfinished"],
         delta=result["unfinished"] - baseline["unfinished"], delta_color="inverse")
c.metric("Capacity bottleneck", result["bottleneck"])
cost = result["cost_per_order"]
d.metric("Labor cost / order", "$" + f"{cost:.2f}" if cost is not None else "N/A")

st.subheader("Station capacity")
st.caption("Theoretical maximum orders per station during one shift.")
max_capacity = max(1, *result["capacity"].values())
for station, capacity in result["capacity"].items():
    st.write(f"**{station}**: {capacity:,} orders")
    st.progress(capacity / max_capacity)

if result["unfinished"]:
    st.warning(
        f"{result['bottleneck']} is the tightest station. "
        f"Estimated unfinished orders: {result['unfinished']:,}."
    )
else:
    st.success("Estimated capacity is enough to handle the arriving orders.")

st.info(
    "Engineering question: If you move one employee between stations, "
    "does output improve, or does a different bottleneck appear? "
    "Change the sliders and compare."
)

report = io.StringIO()
writer = csv.writer(report)
writer.writerow(["Measure", "Normal shift", scenario])
for label, key in [
    ("Incoming orders", "orders"),
    ("Completed orders", "completed"),
    ("Unfinished orders", "unfinished"),
    ("Bottleneck", "bottleneck"),
    ("Labor cost", "labor_cost"),
    ("Cost per order", "cost_per_order"),
]:
    writer.writerow([label, baseline[key], result[key]])
for station in staff:
    writer.writerow([
        station + " capacity",
        baseline["capacity"][station],
        result["capacity"][station],
    ])

st.download_button(
    "Download experiment (.csv)",
    report.getvalue(),
    file_name="flowforge_experiment.csv",
    mime="text/csv",
)

st.caption(
    "MODEL LIMITATION — This is a capacity estimate using fixed processing "
    "times and continuous worker availability. It does not yet model queues, "
    "order arrivals over time, breaks, walking time, or stochastic variation. "
    "Those belong in the next simulation version."
)
