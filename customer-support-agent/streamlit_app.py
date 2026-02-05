import json
import os
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
ROOT_DIR = os.path.dirname(__file__)
CHAT_LOG = os.path.join(ROOT_DIR, "data", "logs", "chats.jsonl")
TICKET_LOG = os.path.join(ROOT_DIR, "data", "logs", "tickets.jsonl")

st.set_page_config(page_title="Support Desk", page_icon=":tools:", layout="wide")

st.markdown(
    """
<style>
:root {
  --bg: #f7f3ee;
  --ink: #1b1b1b;
  --accent: #f05d23;
  --accent-2: #0f4c5c;
  --panel: #fff9f2;
}

.stApp {
  background: linear-gradient(135deg, #f7f3ee 0%, #fff9f2 60%, #f0efe9 100%);
  color: var(--ink);
}

h1, h2, h3, h4, h5 {
  font-family: "Georgia", "Times New Roman", serif;
}

.block-container {
  padding-top: 2rem;
}

/* Make chat text readable on the light theme */
[data-testid="stChatMessage"] {
  color: var(--ink);
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {
  color: var(--ink) !important;
}
[data-testid="stChatMessageContent"] {
  background: var(--panel);
  border: 1px solid #eadfce;
}

.badge {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  letter-spacing: 0.03em;
}

.panel {
  background: var(--panel);
  border: 1px solid #eadfce;
  border-radius: 12px;
  padding: 1rem;
}

.small {
  font-size: 0.85rem;
  color: #5b5b5b;
}

/* Make tables readable in the dashboard */
[data-testid="stTable"] table,
[data-testid="stDataFrame"] table {
  color: var(--ink) !important;
}
[data-testid="stTable"] thead th,
[data-testid="stTable"] tbody td,
[data-testid="stDataFrame"] thead th,
[data-testid="stDataFrame"] tbody td {
  background: var(--panel) !important;
  border-color: #eadfce !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def _read_jsonl(path: str, limit: int | None = None):
    if not os.path.isfile(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit:
        return items[-limit:]
    return items


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1]
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _filter_by_date(items, start_date: date, end_date: date):
    out = []
    for item in items:
        ts = _parse_ts(item.get("timestamp", ""))
        if not ts:
            continue
        if start_date <= ts.date() <= end_date:
            out.append(item)
    return out


def _daily_counts(items):
    counts = defaultdict(int)
    for item in items:
        ts = _parse_ts(item.get("timestamp", ""))
        if not ts:
            continue
        counts[ts.date()] += 1
    return counts


def _date_range_defaults():
    end = date.today()
    start = end - timedelta(days=6)
    return start, end


def _extract_keywords(text: str):
    stop = {
        "the", "and", "a", "an", "to", "of", "in", "on", "for", "is", "are", "was", "were",
        "i", "you", "we", "it", "my", "your", "our", "me", "with", "this", "that", "have",
        "has", "had", "do", "does", "did", "can", "could", "would", "should", "please",
        "help", "support", "ticket", "status", "last", "create",
    }
    tokens = []
    for raw in text.lower().split():
        token = "".join(ch for ch in raw if ch.isalnum())
        if token and token not in stop and len(token) > 2:
            tokens.append(token)
    return tokens


def _stats():
    chats = _read_jsonl(CHAT_LOG)
    tickets = _read_jsonl(TICKET_LOG)
    return {
        "chat_count": len(chats),
        "ticket_count": len(tickets),
        "last_chat": chats[-1]["timestamp"] if chats else "-",
        "last_ticket": tickets[-1]["timestamp"] if tickets else "-",
    }


if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

api_url = API_URL

with st.sidebar:
    st.subheader("Control Panel")
    view = st.radio("View", ["Chat", "Dashboard"], horizontal=True)
    with st.expander("Advanced", expanded=False):
        api_url = st.text_input("API URL", value=api_url)
        if st.button("Reset chat"):
            st.session_state.session_id = None
            st.session_state.messages = []
    st.divider()
    st.subheader("Admin Stats")
    stats = _stats()
    st.write(f"Chats: `{stats['chat_count']}`")
    st.write(f"Tickets: `{stats['ticket_count']}`")
    st.write(f"Last Chat: `{stats['last_chat']}`")
    st.write(f"Last Ticket: `{stats['last_ticket']}`")

if view == "Chat":
    st.title("Support Desk")
    st.markdown("<span class='badge'>RAG + Tickets</span>", unsafe_allow_html=True)
    st.caption("Simple RAG-based support assistant with ticket escalation.")

    left, right = st.columns([2, 1], gap="large")

    with right:
        st.subheader("Recent Tickets")
        tickets = _read_jsonl(TICKET_LOG, limit=20)
        if not tickets:
            st.markdown("<div class='panel small'>No tickets yet.</div>", unsafe_allow_html=True)
        else:
            for t in reversed(tickets):
                st.markdown(
                    f"""
<div class='panel'>
  <div><strong>Ticket {t.get('ticket_id')}</strong></div>
  <div class='small'>{t.get('timestamp', '-')} | session {t.get('session_id', '-')}</div>
  <div style='margin-top:0.5rem'>{t.get('message','')}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

    with left:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Ask a support question...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                resp = requests.post(
                    f"{api_url}/chat",
                    json={"session_id": st.session_state.session_id, "message": prompt},
                    timeout=30,
                )
                if not resp.ok:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text.strip()}")
                try:
                    data = resp.json()
                except Exception:
                    raise RuntimeError(f"Invalid JSON response: {resp.text.strip()}")
                st.session_state.session_id = data.get("session_id")
                answer = data.get("response", "")
                route = data.get("route", "")
                sources = data.get("sources", [])
                ticket_id = data.get("ticket_id")

                assistant_text = answer
                if ticket_id:
                    assistant_text += f"\n\nTicket ID: `{ticket_id}`"
                if sources:
                    src_lines = [f"- {s.get('doc')} #{s.get('chunk_id')}" for s in sources]
                    assistant_text += "\n\nSources:\n" + "\n".join(src_lines)
                if route:
                    assistant_text += f"\n\nRoute: `{route}`"

                st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                with st.chat_message("assistant"):
                    st.markdown(assistant_text)
            except Exception as e:
                err = f"Request failed ({api_url}/chat): {e}"
                st.session_state.messages.append({"role": "assistant", "content": err})
                with st.chat_message("assistant"):
                    st.error(err)
else:
    st.title("Support Ops Overview")
    st.caption("Operational visibility for chats, escalations, and tickets.")

    chats_all = _read_jsonl(CHAT_LOG)
    tickets_all = _read_jsonl(TICKET_LOG)

    default_start, default_end = _date_range_defaults()
    with st.sidebar:
        st.subheader("Filters")
        date_range = st.date_input(
            "Date range",
            value=(default_start, default_end),
        )
        route_filter = st.multiselect(
            "Route",
            options=sorted({c.get("route", "unknown") for c in chats_all}),
            default=[],
        )

    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    chats = _filter_by_date(chats_all, start_date, end_date)
    tickets = _filter_by_date(tickets_all, start_date, end_date)

    if route_filter:
        chats = [c for c in chats if c.get("route") in route_filter]

    unique_sessions = len({c.get("session_id") for c in chats if c.get("session_id")})
    total_chats = len(chats)
    total_tickets = len(tickets)
    escalations = len([c for c in chats if c.get("route") == "escalate"])
    escalation_rate = (total_tickets / total_chats) * 100 if total_chats else 0.0
    avg_resp_len = (
        sum(len(c.get("response", "")) for c in chats) / total_chats if total_chats else 0
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6, gap="small")
    col1.markdown(f"<div class='kpi'><div class='small'>Chats</div><h3>{total_chats}</h3></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='kpi'><div class='small'>Tickets</div><h3>{total_tickets}</h3></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='kpi'><div class='small'>Escalations</div><h3>{escalations}</h3></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='kpi'><div class='small'>Escalation Rate</div><h3>{escalation_rate:.1f}%</h3></div>", unsafe_allow_html=True)
    col5.markdown(f"<div class='kpi'><div class='small'>Avg Response Len</div><h3>{avg_resp_len:.0f}</h3></div>", unsafe_allow_html=True)
    col6.markdown(f"<div class='kpi'><div class='small'>Sessions</div><h3>{unique_sessions}</h3></div>", unsafe_allow_html=True)

    st.divider()

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("Volume Trends")
        chat_counts = _daily_counts(chats)
        ticket_counts = _daily_counts(tickets)
        all_dates = sorted(set(chat_counts) | set(ticket_counts))
        if all_dates:
            chat_series = [chat_counts.get(d, 0) for d in all_dates]
            ticket_series = [ticket_counts.get(d, 0) for d in all_dates]
            st.line_chart({"chats": chat_series, "tickets": ticket_series})
            st.caption("Dates: " + ", ".join(str(d) for d in all_dates))
        else:
            st.info("No activity in the selected date range.")

    with right:
        st.subheader("Quality Signals")
        no_context_rate = (escalations / total_chats) * 100 if total_chats else 0.0
        st.write(f"No-context rate: `{no_context_rate:.1f}%`")

        escalated_msgs = [c.get("user_message", "") for c in chats if c.get("route") == "escalate"]
        keyword_counts = Counter()
        for msg in escalated_msgs:
            keyword_counts.update(_extract_keywords(msg))
        top_keywords = keyword_counts.most_common(5)
        if top_keywords:
            st.markdown("Top escalated keywords:")
            for k, v in top_keywords:
                st.write(f"- `{k}` ({v})")
        else:
            st.write("No escalations to analyze.")

    st.divider()

    left, right = st.columns([2, 1], gap="large")
    with left:
        st.subheader("Recent Chats")
        recent_chats = sorted(chats, key=lambda c: c.get("timestamp", ""), reverse=True)[:15]
        chat_rows = [
            {
                "timestamp": c.get("timestamp", "-"),
                "session": c.get("session_id", "-"),
                "route": c.get("route", "-"),
                "message": (c.get("user_message", "")[:80] + "...") if len(c.get("user_message", "")) > 80 else c.get("user_message", ""),
            }
            for c in recent_chats
        ]
        st.table(chat_rows)

    with right:
        st.subheader("Recent Tickets")
        recent_tickets = sorted(tickets, key=lambda t: t.get("timestamp", ""), reverse=True)[:10]
        ticket_rows = [
            {
                "ticket_id": t.get("ticket_id", "-"),
                "timestamp": t.get("timestamp", "-"),
                "session": t.get("session_id", "-"),
                "message": (t.get("message", "")[:60] + "...") if len(t.get("message", "")) > 60 else t.get("message", ""),
            }
            for t in recent_tickets
        ]
        st.table(ticket_rows)

    st.divider()

    st.subheader("Session Detail")
    session_ids = sorted({c.get("session_id") for c in chats_all if c.get("session_id")})
    selected = st.selectbox("Session ID", options=[""] + session_ids)
    if selected:
        session_chats = [c for c in chats_all if c.get("session_id") == selected]
        session_chats = sorted(session_chats, key=lambda c: c.get("timestamp", ""))
        for c in session_chats:
            st.markdown(
                f"**{c.get('timestamp','-')}** | `{c.get('route','-')}`\n\n"
                f"User: {c.get('user_message','')}\n\n"
                f"Assistant: {c.get('response','')}"
            )
    else:
        st.caption("Select a session to view full transcript.")
