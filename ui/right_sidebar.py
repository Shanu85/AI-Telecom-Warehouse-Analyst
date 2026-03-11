import streamlit as st 
import pandas as pd
import time

def render_chart_panel(df: pd.DataFrame):
    """Render the right-side panel with tabular query results."""

    st.markdown("### 🗂️ Query Results")
    st.caption(f"{len(df)} rows · {len(df.columns)} columns")

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv(index=False),
        file_name="query_results.csv",
        mime="text/csv",
        key=f"download_csv_{int(time.time() * 1000)}"
    )
