import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nlp.intent import IntentClassifier
from nlp.extractor import EntityExtractor
from nlp.profile_builder import ProfileBuilder
from frontend.feedback import init_db, save_feedback


# ── Cache the heavy models so they load once per session, not every rerun ──
@st.cache_resource
def load_pipeline():
    return IntentClassifier(), EntityExtractor(), ProfileBuilder()


intent_clf, extractor, builder = load_pipeline()
init_db()

st.set_page_config(page_title="GovReady", page_icon="🏛️")
st.title("🏛️ GovReady")
st.caption("Tell me what government service you need, in your own words.")

# ── Initialize conversation state (only once per session) ──────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # list of {"role": ..., "content": ...}
    st.session_state.service_id = None
    st.session_state.service_name = None
    st.session_state.collected = {}          # extracted entities so far
    st.session_state.is_complete = False
    st.session_state.final_profile = None

# ── Render past messages ────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── If profile is already complete, show the result and stop ───────────────
if st.session_state.is_complete:
    st.success("✅ Profile complete!")
    st.json(st.session_state.final_profile)

    st.divider()
    st.subheader("📋 Report a discrepancy")
    st.caption("Already visited the office? Let us know if the document list was wrong.")

    with st.form("feedback_form"):
        issue_type = st.selectbox(
            "What happened?",
            ["extra_document_asked", "document_not_needed"],
            format_func=lambda x: (
                "I was asked for an extra document not on the list"
                if x == "extra_document_asked"
                else "A listed document was NOT actually needed"
            ),
        )
        document_name = st.text_input("Which document?")
        notes = st.text_area("Additional notes (optional)")
        submitted = st.form_submit_button("Submit feedback")

        if submitted:
            if document_name.strip() == "":
                st.warning("Please enter a document name.")
            else:
                save_feedback(
                    service_id=st.session_state.service_id,
                    service_name=st.session_state.service_name,
                    issue_type=issue_type,
                    document_name=document_name.strip(),
                    notes=notes.strip(),
                )
                st.success("Thanks — your feedback has been recorded.")

    if st.button("Start over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

# ── Handle new user input ───────────────────────────────────────────────────
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    
# First message: detect intent
    if st.session_state.service_id is None:
        intent = intent_clf.classify(user_input)

        CONFIDENCE_THRESHOLD = 0.4

        if intent["confidence"] < CONFIDENCE_THRESHOLD:
            # Too uncertain to guess — ask for clarification, stay in "no service yet" state
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    "I'm not sure I understood that. Could you tell me which "
                    "government service you need? For example: passport, "
                    "ration card, or driving licence."
                ),
            })
            st.rerun()

        st.session_state.service_id = intent["service_id"]
        st.session_state.service_name = intent["service_name"]

        new_entities = extractor.extract(user_input)
        st.session_state.collected.update(
            {k: v for k, v in new_entities.items() if v is not None}
        )

        assistant_msg = f"Got it — looking into **{intent['service_name']}**."

    # Check what's still missing
    result = builder.build(st.session_state.service_id, st.session_state.collected)

    if result["is_complete"]:
        st.session_state.is_complete = True
        st.session_state.final_profile = {
            "service_id": st.session_state.service_id,
            "service_name": st.session_state.service_name,
            "profile": result["profile"].to_dict(),
        }
        final_msg = "✅ Got everything I need — profile complete!"
        if assistant_msg:
            final_msg = assistant_msg + "\n\n" + final_msg
        st.session_state.messages.append({"role": "assistant", "content": final_msg})
    else:
        question = result["next_question"]
        combined = f"{assistant_msg}\n\n{question}" if assistant_msg else question
        st.session_state.messages.append({"role": "assistant", "content": combined})

    st.rerun()