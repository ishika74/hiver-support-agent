import re
from datetime import datetime

import streamlit as st

from llm_client import call_llm


# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="Spotify AI Support Agent",
    page_icon="🎧",
    layout="wide",
)


# -----------------------------
# Styling
# -----------------------------

st.markdown(
    """
    <style>
    .main {
        background-color: #f7f9f8;
    }

    .stButton > button {
        border-radius: 20px;
        border: 1px solid #d5d9d6;
    }

    .issue-card {
        padding: 15px;
        border-radius: 12px;
        background: #e8f5e9;
        border-left: 5px solid #1db954;
        margin-bottom: 15px;
    }

    .warning-card {
        padding: 15px;
        border-radius: 12px;
        background: #fff3cd;
        border-left: 5px solid #ff9800;
        margin-bottom: 15px;
    }

    .success-card {
        padding: 15px;
        border-radius: 12px;
        background: #e8f5e9;
        border-left: 5px solid #1db954;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Session state
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_intent" not in st.session_state:
    st.session_state.last_intent = "Unknown"

if "last_escalation" not in st.session_state:
    st.session_state.last_escalation = False

if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = ""


# -----------------------------
# Helper functions
# -----------------------------

def classify_issue(message: str) -> str:
    """Simple transparent keyword-based issue classifier."""

    text = message.lower()

    categories = {
        "Playlist problem": [
            "playlist",
            "missing playlist",
            "lost playlist",
            "playlist disappeared",
            "can't find my playlist",
        ],
        "Playback problem": [
            "skipping",
            "song stops",
            "music stops",
            "buffering",
            "not playing",
            "playback",
            "audio problem",
        ],
        "Login or account problem": [
            "login",
            "log in",
            "sign in",
            "password",
            "account",
            "locked out",
        ],
        "Payment problem": [
            "payment",
            "charged",
            "billing",
            "premium payment",
            "subscription",
            "refund",
        ],
        "App or technical problem": [
            "crash",
            "crashing",
            "freeze",
            "frozen",
            "not opening",
            "error",
            "bug",
        ],
        "Download or offline problem": [
            "download",
            "offline",
            "downloaded songs",
        ],
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "General support"


def should_escalate(message: str) -> bool:
    """Detect cases that may require human support."""

    text = message.lower()

    escalation_keywords = [
        "hacked",
        "account stolen",
        "unauthorized payment",
        "fraud",
        "chargeback",
        "legal",
        "data breach",
        "can't access my account",
        "account suspended",
        "refund",
        "still not working",
        "human agent",
        "talk to a person",
        "support agent",
    ]

    return any(keyword in text for keyword in escalation_keywords)


def create_ticket(messages, intent, escalation):
    """Create a support-ticket summary from the current conversation."""

    conversation_text = "\n".join(
        f'{item["role"].upper()}: {item["content"]}'
        for item in messages
    )

    ticket_id = datetime.now().strftime("SPOT-%Y%m%d-%H%M%S")

    return f"""Spotify Support Ticket

Ticket ID: {ticket_id}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Issue category: {intent}
Escalation required: {"Yes" if escalation else "Not currently detected"}

Conversation:
{conversation_text}

Recommended next action:
{"Review by a human support agent is recommended." if escalation else "Continue troubleshooting and ask for more details if required."}
"""


def get_conversation_text():
    recent_messages = st.session_state.messages[-8:]

    return "\n".join(
        f'{message["role"].capitalize()}: {message["content"]}'
        for message in recent_messages
    )


def ask_support_agent(user_message):
    intent = classify_issue(user_message)
    escalation = should_escalate(user_message)

    st.session_state.last_intent = intent
    st.session_state.last_escalation = escalation

    conversation = get_conversation_text()

    escalation_instruction = ""

    if escalation:
        escalation_instruction = """
The issue may require human support. Clearly tell the customer that
a human support agent may need to review the issue. Do not claim that
a ticket has actually been submitted.
"""

    prompt = f"""
You are a professional Spotify customer-support AI assistant.

Your goals:
- Understand the customer's latest message.
- Give friendly, accurate, practical troubleshooting steps.
- Use short numbered steps where useful.
- Do not claim to access the customer's Spotify account.
- Do not claim to issue refunds or change account settings.
- Do not invent policies.
- Ask one useful follow-up question when necessary.
- Avoid repeating the same troubleshooting advice unnecessarily.

Detected issue category:
{intent}

{escalation_instruction}

Conversation:
{conversation}

Latest customer message:
{user_message}

Write the best possible customer-support response.
"""

    return call_llm(prompt)


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:
    st.header("🎧 Support Controls")

    st.write("Choose a common customer issue:")

    quick_issues = {
        "🎵 Songs are skipping": "Hi, my songs are skipping after some time.",
        "📂 Missing playlist": "I can't find my playlist.",
        "🔐 Login problem": "I cannot log in to my Spotify account.",
        "💳 Payment problem": "I was charged incorrectly for Premium.",
        "📱 App crashing": "The Spotify app keeps crashing.",
        "⬇️ Offline downloads": "My downloaded songs are not playing offline.",
    }

    for label, issue in quick_issues.items():
        if st.button(label, use_container_width=True):
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": issue,
                }
            )

            with st.spinner("Generating support response..."):
                answer = ask_support_agent(issue)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            st.rerun()

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_intent = "Unknown"
        st.session_state.last_escalation = False
        st.session_state.last_ticket = ""
        st.rerun()

    st.divider()

    st.subheader("Current analysis")
    st.write(f"**Issue:** {st.session_state.last_intent}")

    if st.session_state.last_escalation:
        st.warning("Human support review may be required.")
    else:
        st.success("No escalation trigger detected.")


# -----------------------------
# Main interface
# -----------------------------

st.title("🎧 Spotify AI Support Agent")
st.caption("AI-powered customer-support assistant with issue detection and escalation support")


if not st.session_state.messages:
    st.markdown(
        """
        <div class="success-card">
        <b>Welcome!</b><br>
        Describe your Spotify issue below, or select a common issue from the sidebar.
        </div>
        """,
        unsafe_allow_html=True,
    )


# Display chat history

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------
# Chat input
# -----------------------------

user_message = st.chat_input("Describe your Spotify problem...")


if user_message:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    intent = classify_issue(user_message)
    escalation = should_escalate(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your issue and preparing a response..."):
            answer = ask_support_agent(user_message)

        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    st.rerun()


# -----------------------------
# Post-response tools
# -----------------------------

if st.session_state.messages:
    st.divider()

    st.subheader("Response tools")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👍 Helpful", use_container_width=True):
            st.success("Thanks for your feedback!")

    with col2:
        if st.button("👎 Not helpful", use_container_width=True):
            st.warning("Feedback recorded. Consider escalating this issue.")

    with col3:
        if st.button("🎫 Create support ticket", use_container_width=True):
            ticket = create_ticket(
                st.session_state.messages,
                st.session_state.last_intent,
                st.session_state.last_escalation,
            )

            st.session_state.last_ticket = ticket
            st.success("Support-ticket summary created.")


# -----------------------------
# Ticket display and download
# -----------------------------

if st.session_state.last_ticket:
    st.divider()
    st.subheader("🎫 Support-ticket summary")

    st.text_area(
        "Ticket details",
        value=st.session_state.last_ticket,
        height=300,
    )

    st.download_button(
        label="Download ticket as TXT",
        data=st.session_state.last_ticket,
        file_name="spotify_support_ticket.txt",
        mime="text/plain",
    )