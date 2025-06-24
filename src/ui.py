import streamlit as st
import pandas as pd
from typing import Optional


def paginated_dataframe(df: pd.DataFrame, key_prefix: str, page_size: int = 20, column_aliases: Optional[dict] = None):
    total_rows = len(df)
    if f"{key_prefix}_page_number" not in st.session_state:
        st.session_state[f"{key_prefix}_page_number"] = 1

    if total_rows > 0:
        total_pages = (total_rows - 1) // page_size + 1
    else:
        total_pages = 1

    # --- Display DataFrame slice ---
    start_index = (st.session_state[f"{key_prefix}_page_number"] - 1) * page_size
    end_index = min(start_index + page_size, total_rows)

    column_config = None
    if column_aliases:
        column_config = {
            old_name: st.column_config.Column(label=new_name)
            for old_name, new_name in column_aliases.items()
        }

    st.dataframe(
        df.iloc[start_index:end_index],
        column_config=column_config
    )

    # --- Pagination Controls ---
    col1, col2, col3, col4 = st.columns([1, 1, 1, 5])

    with col1:
        if st.button("⬅️", key=f"{key_prefix}_prev"):
            if st.session_state[f"{key_prefix}_page_number"] > 1:
                st.session_state[f"{key_prefix}_page_number"] -= 1

    with col2:
        if st.button("➡️", key=f"{key_prefix}_next"):
            if st.session_state[f"{key_prefix}_page_number"] < total_pages:
                st.session_state[f"{key_prefix}_page_number"] += 1

    with col3:
        page_num_str = f"Page {st.session_state[f'{key_prefix}_page_number']}/{total_pages}"
        st.markdown(f"<p style='text-align: center; margin-top: 5px;'>{page_num_str}</p>", unsafe_allow_html=True) 