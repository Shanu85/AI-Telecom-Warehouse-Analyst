import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from data.schema_definitions import schema
from data.duckdb_manager import DuckDBManager
from scripts.llm_client import LLM_Client
from scripts.vector_client import VectorStore
from left_sidebar import render_left_sidebar
import pandas as pd
from right_sidebar import render_chart_panel
from feedback import show_feedback_buttons,render_confidence_badge

@st.cache_resource
def get_db():
    return DuckDBManager()

@st.cache_resource
def get_llm_client():
    return LLM_Client()

@st.cache_resource
def get_vector_client():
    return VectorStore()


def handle_user_query(user_question,db,main_col, chart_col):
    if user_question:
        # Reset feedback state for the new query
        st.session_state.feedback_given = False
        st.session_state.pending_feedback = None

        if not st.session_state.selected_tables:
            with main_col:
                st.error("⚠️ Please select at least one table.")
        else:
            client = get_llm_client()
            vector_client = get_vector_client()
            answer = ""
            sql = ""
            success = False

            with main_col:
                with st.status("Thinking...", expanded=True) as status:
                    try:
                        #Grab last 3 Q&A pairs (6 messages: 3 user + 3 assistant)
                        recent_chat_history=st.session_state.chat_history[-6:] 

                        st.write("📐 Extracting schema for selected tables...")
                        schema_text = client.get_table_schemas_text(
                            st.session_state.selected_tables, db
                        )

                        st.write("🧠 Generating SQL query...")
                        sql, results,confidence = client.generate_sql_with_retries(
                            user_question, schema_text, db,vector_client,recent_chat_history
                        )

                        st.session_state.last_confidence = confidence
                
                        st.write(f"✅ SQL generated — {len(results)} rows returned")

                        st.write("💬 Generating plain English answer...")
                        answer = client.generate_answer(user_question, sql, results,recent_chat_history)

                        # ✅ Store results in session state for chart panel
                        st.session_state.last_results_df = pd.DataFrame(results) if results else pd.DataFrame()

                        # ✅ Store pending feedback — do NOT add to ChromaDB yet
                        # ChromaDB indexing only happens on 👍 click
                        st.session_state.pending_feedback = {
                            "question": user_question,
                            "sql":      sql,
                            "tables":   st.session_state.selected_tables,
                            "answer":   answer
                        }

                        success = True

                    except Exception as e:
                        answer = f"❌ Something went wrong: {e}"
                        sql = ""
                    
                    if success:
                        status.update(
                            label=f"✅ Done · via {client.last_provider_used}",
                            state="complete",
                            expanded=False
                        )
                    else:
                        status.update(label="❌ Failed", state="error")

        
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.session_state.last_sql = sql
            st.session_state.last_provider_used = client.last_provider_used or ""
            # Rerun so layout rebuilds with fresh session state
            st.rerun()

        # df = st.session_state.get("last_results_df", pd.DataFrame())
        # if not df.empty and len(df) > 1:
        #     with chart_col:
        #         render_chart_panel(df)

def main():
    st.set_page_config(
    page_title="Warehouse Analyst",
    layout="wide")

    st.title("📊 AI Telecom Warehouse Analyst")
    st.caption("Ask questions about your warehouse in plain English")

    # ---------- Session State ---------- maintains user I/P
    defaults = {
        "chat_history": [],
        "selected_tables": [],
        "last_sql": "",
        "last_provider_used": "",
        "last_results_df": pd.DataFrame(),
        "feedback_given": False,
        "pending_feedback": None,
        'last_confidence':dict()
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    db = get_db()
    
    # ---------- Sidebar ----------
            
    render_left_sidebar(db)

    # ---------- Main Layout: chat | chart ----------
    df = st.session_state.get("last_results_df", pd.DataFrame())
    has_chart = not df.empty and len(df) > 1

    if has_chart:
        main_col, chart_col = st.columns([1.2, 1], gap="large")
    else:
        main_col = st.container()
        chart_col = None

    # ---------- Chat area ----------
    with main_col:
        st.subheader("💬 Ask your question")

        # Show last used LLM + SQL expander
        if st.session_state.last_provider_used:
            st.caption(f"⚡ Answered by: **{st.session_state.last_provider_used}**")
        
        # Show SQL used for the last query
        if st.session_state.last_sql:
            with st.expander("🔍 Last SQL Query", expanded=False):
                st.code(st.session_state.last_sql, language="sql")

        render_confidence_badge(st.session_state.get("last_confidence", {}))

        # Render chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        show_feedback_buttons(get_vector_client(),db)


    # ---------- Persistent chart panel (rerenders on every run) ----------
    if has_chart and chart_col:
        with chart_col:
            render_chart_panel(df)

    user_question = st.chat_input(
        "Example: Top vendors by payout in Maharashtra"
    )


    handle_user_query(user_question,db,main_col, chart_col if has_chart else st.container())

    #print(st.session_state.last_results_df)


if __name__=='__main__':
    main()
