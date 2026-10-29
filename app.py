"""Lemons Dealership Simulation — Streamlit + Supabase classroom prototype."""
import hashlib
import hmac
import secrets

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Lemons Dealership", page_icon="🚗", layout="wide")
STAGES = ["Round 1", "Round 2", "Relocation", "Round 3", "Regulation announcement", "Round 4", "Round 5", "Round 6", "Round 7"]
ROUND_STAGE = {1: 1, 2: 2, 3: 4, 4: 6, 5: 7, 6: 8, 7: 9}
BUDGET = 20000


def password_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@st.cache_resource
def database():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def rows(table, **filters):
    query = database().table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute().data or []


def settings():
    return rows("sim_settings", id=1)[0]


def decisions(team_id):
    return sorted(rows("decisions", team_id=team_id), key=lambda x: x["round"])


def relocation(team_id):
    records = rows("relocations", team_id=team_id)
    return records[0]["relocate"] if records else None


def customers_for_round(round_num, prior, moved):
    customers = 10
    for entry in prior:
        if entry["round"] >= round_num:
            break
        if entry["round"] == 2 and moved:
            customers = 10
        customers = max(2, customers - entry["undisclosed"])
    if round_num == 3 and moved:
        customers = 10
    return customers


def round_numbers(stage):
    return [n for n, s in ROUND_STAGE.items() if s <= stage]


def results(prior, moved, stage):
    visible = [d for d in prior if ROUND_STAGE[d["round"]] < stage]
    profit = sum(d["operating_profit"] - d["fine"] for d in visible)
    if moved and stage > 3:
        profit -= 20000
    return profit, visible


def student():
    st.subheader("Your dealership")
    if "team_id" not in st.session_state:
        with st.form("join"):
            name = st.text_input("Dealership name (use a fictional name)").strip()
            pin = st.text_input("Team PIN (choose one and reuse it)", type="password")
            join = st.text_input("Class join code", type="password")
            submitted = st.form_submit_button("Join dealership")
        if submitted:
            if not hmac.compare_digest(join, st.secrets["TEAM_JOIN_CODE"]):
                st.error("Incorrect class join code.")
            elif len(name) < 3 or len(pin) < 6:
                st.error("Use a dealership name of at least 3 characters and a PIN of at least 6 characters.")
            else:
                existing = rows("teams", name=name)
                if existing:
                    if hmac.compare_digest(existing[0]["pin_hash"], password_hash(pin)):
                        st.session_state.team_id = existing[0]["id"]
                        st.session_state.team_name = name
                        st.rerun()
                    else:
                        st.error("That dealership name is already taken or the PIN is incorrect.")
                else:
                    try:
                        created = database().table("teams").insert({"name": name, "pin_hash": password_hash(pin)}).execute().data[0]
                        st.session_state.team_id = created["id"]
                        st.session_state.team_name = name
                        st.rerun()
                    except Exception:
                        st.error("Could not create dealership. Try another name.")
        return

    team_id = st.session_state.team_id
    st.caption(f"Signed in as {st.session_state.team_name}")
    if st.button("Switch dealership"):
        for key in ("team_id", "team_name"):
            st.session_state.pop(key, None)
        st.rerun()
    config = settings()
    stage = config["stage"]
    prior = decisions(team_id)
    moved = relocation(team_id)
    total, visible = results(prior, moved, stage)
    c1, c2 = st.columns(2)
    c1.metric("Cumulative net profit (revealed)", f"${total:,}")
    c2.metric("Current event", STAGES[stage - 1])
    if visible:
        st.markdown("#### Completed rounds")
        st.dataframe(pd.DataFrame([{
            "Round": d["round"], "Customers": d["customers"],
            "Reliable": d["reliable"], "Disclosed": d["disclosed"],
            "Undisclosed": d["undisclosed"], "Operating profit": d["operating_profit"],
            "Inspected": "Yes" if d["inspected"] else ("No" if d["inspected"] is False else "N/A"),
            "Fine": d["fine"],
        } for d in visible]), hide_index=True, use_container_width=True)
    if stage == 3:
        st.markdown("### Relocation decision")
        st.write("You may relocate to a new jurisdiction for a one-time **$20,000** charge. Relocation restores your customer base to 10 at the start of Round 3. Future rules are not yet known.")
        if moved is not None:
            st.success("Relocation decision submitted. Wait for your instructor to advance.")
        else:
            choice = st.radio("Your decision", ["Stay", "Relocate"])
            if st.button("Submit final relocation decision", type="primary"):
                try:
                    database().table("relocations").insert({"team_id": team_id, "relocate": choice == "Relocate"}).execute()
                    st.rerun()
                except Exception:
                    st.error("Could not submit. Refresh and try again.")
        return
    if stage == 5:
        st.markdown("### New regulatory environment")
        if moved is None:
            st.warning("Your relocation decision is missing. Contact the instructor.")
        elif moved:
            st.warning("**State B:** Beginning in Round 4, selling known defective vehicles without disclosure is illegal. Each round, your dealership has a 20% chance of inspection. If inspected, you pay **$10,000 per undisclosed lemon** sold that round.")
        else:
            st.info("**State A:** There is no new mandatory disclosure rule or inspection fine. Undisclosed lemons still reduce future customers through word of mouth.")
        st.write("Wait for your instructor to open Round 4.")
        return
    round_num = next((r for r, s in ROUND_STAGE.items() if s == stage), None)
    if round_num is None:
        return
    if round_num >= 3 and moved is None:
        st.warning("Your relocation decision is missing. Contact the instructor.")
        return
    if any(d["round"] == round_num for d in prior):
        st.success("Your decision is locked. Wait for your instructor to advance to reveal the result.")
        return
    available = customers_for_round(round_num, prior, moved)
    st.markdown(f"### Round {round_num}: Purchase vehicles")
    st.write(f"**Customers available:** {available}  ·  **Purchasing budget:** $20,000")
    if round_num >= 4 and moved:
        st.warning("State B: 20% chance of inspection; $10,000 fine per undisclosed lemon if inspected.")
    with st.form(f"round_{round_num}"):
        a = st.number_input("Reliable cars — buy $7,500 / sell $17,500", min_value=0, max_value=10, step=1)
        b = st.number_input("Disclosed lemons — buy $2,500 / sell $5,000", min_value=0, max_value=10, step=1)
        c = st.number_input("Undisclosed lemons — buy $2,500 / sell $7,500", min_value=0, max_value=10, step=1)
        cost = 7500 * a + 2500 * (b + c)
        profit = 10000 * a + 2500 * b + 5000 * c
        st.write(f"**Purchasing cost:** ${cost:,} · **Operating profit before fines:** ${profit:,} · **Cars:** {a+b+c}/{available}")
        confirm = st.checkbox("Our team has finalized this decision. It cannot be changed.")
        submit = st.form_submit_button("Submit final decision", type="primary")
    if submit:
        if not confirm:
            st.error("Confirm that your decision is final.")
        elif cost > BUDGET or a + b + c > available:
            st.error("Purchasing cost exceeds $20,000 or vehicle count exceeds available customers.")
        else:
            inspected = secrets.randbelow(100) < 20 if round_num >= 4 and moved else None
            fine = 10000 * c if inspected else 0
            try:
                database().table("decisions").insert({"team_id": team_id, "round": round_num,
                    "reliable": int(a), "disclosed": int(b), "undisclosed": int(c),
                    "customers": available, "cost": cost, "operating_profit": profit,
                    "inspected": inspected, "fine": fine}).execute()
                st.rerun()
            except Exception:
                st.error("Decision not saved. It may already have been submitted; refresh to check.")


def instructor():
    if not st.session_state.get("instructor_auth"):
        with st.form("instructor_login"):
            pwd = st.text_input("Instructor password", type="password")
            submit = st.form_submit_button("Sign in")
        if submit:
            if hmac.compare_digest(pwd, st.secrets["INSTRUCTOR_PASSWORD"]):
                st.session_state.instructor_auth = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return
    if st.button("Sign out of instructor view"):
        st.session_state.instructor_auth = False
        st.rerun()
    config = settings()
    stage = config["stage"]
    st.subheader("Instructor dashboard")
    st.info(f"Current stage: **{STAGES[stage - 1]}**")
    teams = rows("teams")
    all_decisions = rows("decisions")
    relocations = rows("relocations")
    relocation_map = {r["team_id"]: r["relocate"] for r in relocations}
    current_round = next((r for r, s in ROUND_STAGE.items() if s == stage), None)
    status = []
    for team in teams:
        tid = team["id"]
        team_decisions = [d for d in all_decisions if d["team_id"] == tid]
        done = (any(d["round"] == current_round for d in team_decisions) if current_round
                else tid in relocation_map if stage == 3 else True)
        total = sum(d["operating_profit"] - d["fine"] for d in team_decisions)
        if relocation_map.get(tid):
            total -= 20000
        status.append({"Dealership": team["name"], "Submitted current stage": done,
                       "Relocated": relocation_map.get(tid, "Pending"),
                       "Total net profit (including hidden outcomes)": total})
    if status:
        st.dataframe(pd.DataFrame(status), hide_index=True, use_container_width=True)
    else:
        st.write("No dealerships have joined yet.")
    pending = [s["Dealership"] for s in status if not s["Submitted current stage"]]
    if pending:
        st.warning("Awaiting submission: " + ", ".join(pending))
    if stage < 9:
        st.write(f"Next stage: **{STAGES[stage]}**")
        acknowledge = st.checkbox("I understand advancing will lock the current stage for all teams.")
        if st.button("Advance everyone to next stage", disabled=bool(pending) or not acknowledge, type="primary"):
            database().table("sim_settings").update({"stage": stage + 1}).eq("id", 1).execute()
            st.rerun()
    else:
        st.success("Round 7 is open. You may end the activity whenever ready.")
    st.markdown("### Download instructor report")
    export = []
    for d in all_decisions:
        team = next((t for t in teams if t["id"] == d["team_id"]), None)
        export.append({"dealership": team["name"] if team else d["team_id"],
                       "relocated": relocation_map.get(d["team_id"]),
                       **{k: d[k] for k in ("round", "customers", "reliable", "disclosed", "undisclosed", "cost", "operating_profit", "inspected", "fine", "created_at")}})
    st.download_button("Download decisions as CSV", pd.DataFrame(export).to_csv(index=False).encode("utf-8"),
                       file_name="lemons_dealership_results.csv", mime="text/csv")
    st.caption("Independent inspections are generated and stored when each team submits. Students see results only after the stage advances. Do not reveal the available total number of rounds.")


st.title("🚗 Lemons Dealership Simulation")
st.caption("A classroom simulation of disclosure, reputation, relocation, and regulation")
try:
    role = st.sidebar.radio("Choose view", ["Student", "Instructor"])
    st.sidebar.button("Refresh status", on_click=st.rerun)
    if role == "Student":
        student()
    else:
        instructor()
except KeyError as exc:
    st.error(f"Missing Streamlit secret: {exc}. See README.md for setup instructions.")
except Exception as exc:
    st.error("Could not connect to the simulation database. Verify Streamlit secrets and run schema.sql in Supabase.")
    st.caption(type(exc).__name__)
