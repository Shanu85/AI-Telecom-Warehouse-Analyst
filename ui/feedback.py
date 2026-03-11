import streamlit as st
from scripts.vector_client import VectorStore
from data.duckdb_manager import DuckDBManager

"""
    Show 👍 / 👎 buttons after each answer.
    - 👍 → saves to DuckDB + indexes in ChromaDB (becomes a few-shot example)
    - 👎 → saves to DuckDB only (never used as an example)
"""

def show_feedback_buttons(vector_store: VectorStore, db: DuckDBManager):
    # Only show if we have a pending answer and feedback hasn't been given yet
    if not st.session_state.get("pending_feedback"):
        return

    if st.session_state.feedback_given:
        return

    st.write("Was this answer helpful?")
    col1, col2 = st.columns(2)

    if col1.button("👍 Yes"):
        # FIX: Wrap ChromaDB + DuckDB writes in try/except independently.
        # ChromaDB failure (disk issue, cold start) should not silently crash the UI.
        chroma_ok = True
        try:
            vector_store.add_documents({
                "user_question": st.session_state.pending_feedback["question"],
                "sql_generated": st.session_state.pending_feedback["sql"],
                "table_used":    st.session_state.pending_feedback["tables"],
                "answer":        st.session_state.pending_feedback["answer"]
            })
        except Exception as e:
            chroma_ok = False
            st.warning(f"⚠️ Could not save to vector store: {e}")

        try:
            db.save_feedback(
                question=st.session_state.pending_feedback["question"],
                sql=st.session_state.pending_feedback["sql"],
                answer=st.session_state.pending_feedback["answer"],
                rating=1
            )
        except Exception as e:
            st.warning(f"⚠️ Could not save feedback to DB: {e}")

        st.session_state.feedback_given = True

        if chroma_ok:
            st.success(
                f"✅ Saved as training example! ({vector_store.collection.count()} total in memory)"
            )
        else:
            st.info("✅ Feedback recorded (audit only — vector store unavailable).")

    if col2.button("👎 No"):
        # Save to DuckDB only — skips ChromaDB
        try:
            db.save_feedback(
                question=st.session_state.pending_feedback["question"],
                sql=st.session_state.pending_feedback["sql"],
                answer=st.session_state.pending_feedback["answer"],
                rating=0
            )
        except Exception as e:
            st.warning(f"⚠️ Could not save feedback to DB: {e}")

        st.session_state.feedback_given = True
        st.info("👎 Noted — won't use this as a future example.")


def render_confidence_badge(confidence: dict):
    """Render a visual confidence indicator below the SQL expander."""
    if not confidence or confidence["score"] is None:
        return
    
    score = confidence["score"]
    reason = confidence["reason"]
    assumptions = confidence["assumptions"]

    # Color logic
    if score >= 8:
        color, label, icon = "green",  "High Confidence",   "✅"
    elif score >= 6:
        color, label, icon = "orange", "Medium Confidence", "⚠️"
    else:
        color, label, icon = "red",    "Low Confidence",    "🚨"
    

    # Badge
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {color};
            padding: 8px 14px;
            border-radius: 4px;
            background-color: {'#f0fff0' if color == 'green' else '#fff8f0' if color == 'orange' else '#fff0f0'};
            margin: 8px 0;
        ">
            <strong style="color: #1a1a1a;">{icon} {label}: {score}/10</strong><br/>
            <span style="font-size: 0.9em; color: #444;">{reason}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Show assumptions if any
    if assumptions:
        with st.expander("📌 Assumptions made", expanded=(color == "red")):
            for a in assumptions:
                st.caption(f"• {a}")
    
    # Hard warning banner for low confidence
    if score < 6:
        st.warning(
            "⚠️ Low confidence — the SQL may not fully reflect your question. "
            "Try rephrasing or selecting different tables."
        )
