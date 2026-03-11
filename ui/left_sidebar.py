import streamlit as st
from data.schema_definitions import schema


def select_tables_sidebar():
    # ---------- Sidebar ----------
    st.sidebar.header("📂 Data Source")
    available_tables = [table for table in schema.keys()]

    selected_tables = st.sidebar.multiselect(
        "Select Tables",
        available_tables,default=st.session_state.selected_tables)

    st.session_state.selected_tables=selected_tables


def schema_preview_sidebar(db):
    st.sidebar.subheader("📘 Schema Preview")
    available_tables = [table for table in schema.keys()]

    table_name = st.sidebar.selectbox(
        "Select Table",
        available_tables,index=None)
    
    table_schema = db.get_table_schema(table_name)
    with st.sidebar.expander(f"🔹 {table_name}", expanded=False):
        for col in table_schema:
            st.caption(f"{col['column']} ({col['type']})")

def render_left_sidebar(db):
    select_tables_sidebar()

    st.sidebar.divider()

    schema_preview_sidebar(db)

    st.sidebar.divider()

    st.sidebar.subheader("🧠 Business Glossary")
    st.sidebar.caption("shape → calculated length")
