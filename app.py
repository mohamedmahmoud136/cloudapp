"""
app.py – Streamlit UI for the Data Storage & Sharing System.

All business logic lives in logic.py; this file handles only the
presentation layer.
"""

import streamlit as st
import pandas as pd
from typing import List

from logic import (
    TEAM_MAX,
    ORG_MAX,
    SMALL_SIZE_MB,
    MEDIUM_SIZE_MB,
    get_share_level,
    get_storage_method,
    build_report,
    needs_warning,
    total_size,
    largest_record,
    search_by_name,
)

# ------------------------------------------------------------------
# Page configuration  (must be the first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Data Storage & Sharing System",
    page_icon="🗂️",
    layout="wide",
)

# ------------------------------------------------------------------
# Session state initialisation
# ------------------------------------------------------------------
if "records" not in st.session_state:
    st.session_state["records"]: List[dict] = []

if "confirm_clear" not in st.session_state:
    st.session_state["confirm_clear"] = False


# ------------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------------
def _existing_names() -> List[str]:
    """Return lowercase names of all current records."""
    return [r["name"].lower() for r in st.session_state["records"]]


def _storage_badge(method: str) -> str:
    """Return an HTML-coloured badge for the storage method."""
    colour_map = {
        "Local Storage": "#28a745",   # green
        "Shared Storage": "#007bff",  # blue
        "Cloud Storage": "#6f42c1",   # purple
    }
    colour = colour_map.get(method, "#6c757d")
    return (
        f'<span style="background-color:{colour};color:#fff;'
        f'padding:2px 10px;border-radius:12px;font-weight:600;">'
        f"{method}</span>"
    )


def _render_report_card(record: dict, key_prefix: str = "") -> None:
    """Render a single report card inside an expander."""
    report = build_report(record)
    method = report["Suggested Storage Method"]

    st.markdown(f"**Data Name:** {report['Data Name']}")
    st.markdown(f"**Size (MB):** {report['Size (MB)']}")
    st.markdown(f"**Number of Users:** {report['Number of Users']}")
    st.markdown(f"**Access Type:** {report['Access Type']}")
    st.markdown(f"**Share Level:** {report['Share Level']}")
    st.markdown(
        f"**Suggested Storage Method:** {_storage_badge(method)}",
        unsafe_allow_html=True,
    )

    # Warning for multi-user write access
    if needs_warning(record):
        st.warning(
            "⚠️ WARNING: Multiple users can edit this data! "
            "Use version control and regular backups, and restrict "
            "write access to avoid wrong edits or data loss."
        )

    # Per-record .txt download
    txt = "\n".join(f"{k}: {v}" for k, v in report.items())
    st.download_button(
        label="💾 Download report (.txt)",
        data=txt,
        file_name=f"{record['name']}_report.txt",
        mime="text/plain",
        key=f"dl_{key_prefix}_{record['name']}",
    )


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.header("📖 About")
    st.info(
        "Register data assets, determine share levels, get storage "
        "method suggestions, and track statistics — all in one place."
    )

    st.subheader("⚙️ Current Thresholds")
    st.markdown(
        f"- **Team max users:** {TEAM_MAX}\n"
        f"- **Organization max users:** {ORG_MAX}\n"
        f"- **Local storage limit:** {SMALL_SIZE_MB} MB\n"
        f"- **Shared storage limit:** {MEDIUM_SIZE_MB} MB"
    )

    st.divider()

    # Clear all records with confirmation
    if not st.session_state["confirm_clear"]:
        if st.button("🧹 Clear all records"):
            st.session_state["confirm_clear"] = True
            st.rerun()
    else:
        st.warning("⚠️ This will delete **ALL** records.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Yes, clear"):
                st.session_state["records"] = []
                st.session_state["confirm_clear"] = False
                st.rerun()
        with col_no:
            if st.button("❌ Cancel"):
                st.session_state["confirm_clear"] = False
                st.rerun()


# ------------------------------------------------------------------
# Main title
# ------------------------------------------------------------------
st.title("🗂️ Data Storage & Sharing System")

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_add, tab_reports, tab_stats = st.tabs(
    ["➕ Add Record", "📊 Reports", "🔎 Statistics & Search"]
)

# ==================================================================
# TAB 1 – Add Record
# ==================================================================
with tab_add:
    st.header("Add a New Data Record")

    with st.form(key="add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            inp_name = st.text_input("Data name", placeholder="e.g. Sales Report")
        with col2:
            inp_access = st.selectbox("Access type", ["Read Only", "Read & Write"])

        inp_users = st.number_input(
            "Number of users", min_value=1, value=1, step=1, format="%d"
        )
        inp_size = st.number_input(
            "Data size (MB)", min_value=0.01, value=100.0, step=0.01, format="%.2f"
        )

        submitted = st.form_submit_button("Add Record")

    # Validation runs outside the form context so error messages persist
    if submitted:
        errors: List[str] = []
        clean_name = inp_name.strip()

        if not clean_name:
            errors.append("❌ Data name cannot be empty.")
        elif clean_name.lower() in _existing_names():
            errors.append(
                f"❌ A record named **\"{clean_name}\"** already exists (case-insensitive)."
            )
        if inp_users < 1:
            errors.append("❌ Number of users must be at least 1.")
        if inp_size <= 0:
            errors.append("❌ Data size must be greater than 0 MB.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state["records"].append(
                {
                    "name": clean_name,
                    "users": int(inp_users),
                    "size": float(inp_size),
                    "access": inp_access,
                }
            )
            st.success(f"✅ Record **\"{clean_name}\"** added successfully!")
            st.rerun()

    st.divider()

    # Load sample data
    st.subheader("💡 Quick Start")
    if st.button("Load sample data"):
        samples = [
            {"name": "Photos", "users": 1, "size": 200.0, "access": "Read Only"},
            {"name": "Sales", "users": 8, "size": 2000.0, "access": "Read & Write"},
            {"name": "Logs", "users": 500, "size": 20000.0, "access": "Read & Write"},
        ]
        added = 0
        existing = _existing_names()
        for s in samples:
            if s["name"].lower() not in existing:
                st.session_state["records"].append(s)
                existing.append(s["name"].lower())
                added += 1
        if added:
            st.success(f"✅ {added} sample record(s) added.")
            st.rerun()
        else:
            st.info("Sample data already loaded – no duplicates added.")


# ==================================================================
# TAB 2 – Reports
# ==================================================================
with tab_reports:
    st.header("Record Reports")
    records = st.session_state["records"]

    if not records:
        st.info("🗂️ No records yet — add some in the **Add Record** tab.")
    else:
        # Warning summary at the top
        warn_count = sum(1 for r in records if needs_warning(r))
        if warn_count:
            st.warning(
                f"⚠️ **{warn_count}** record(s) have write-access warnings. "
                "Review them below."
            )
        else:
            st.success("✅ No write-access warnings across all records.")

        # Individual report cards
        for idx, rec in enumerate(records):
            share = get_share_level(rec["users"])
            method = get_storage_method(rec["size"], rec["users"])
            label = f"📄 {rec['name']}  —  {share} · {method}"
            with st.expander(label, expanded=False):
                _render_report_card(rec, key_prefix=f"rep_{idx}")


# ==================================================================
# TAB 3 – Statistics & Search
# ==================================================================
with tab_stats:
    st.header("Overall Statistics")
    records = st.session_state["records"]

    # Metric cards
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Records", len(records))
    col_b.metric("Total Size (MB)", f"{total_size(records):,.2f}")

    largest = largest_record(records)
    if largest:
        col_c.metric("Largest Record", f"{largest['name']} ({largest['size']:,.2f} MB)")
    else:
        col_c.metric("Largest Record", "N/A")

    st.divider()

    # Summary table
    if records:
        st.subheader("📋 Summary Table")
        rows = []
        for r in records:
            rows.append(
                {
                    "Name": r["name"],
                    "Users": r["users"],
                    "Size (MB)": r["size"],
                    "Access": r["access"],
                    "Share Level": get_share_level(r["users"]),
                    "Storage Method": get_storage_method(r["size"], r["users"]),
                }
            )
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # CSV export
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export all records as CSV",
            data=csv_data,
            file_name="data_records.csv",
            mime="text/csv",
        )
    else:
        st.info("No records to display yet.")

    st.divider()

    # Search
    st.subheader("🔍 Search a Record")
    search_term = st.text_input(
        "Enter a data name to search (case-insensitive)",
        key="search_input",
    )
    if st.button("Search", key="search_btn"):
        if not search_term.strip():
            st.error("Please enter a name to search.")
        else:
            exact, partials = search_by_name(records, search_term)
            if exact:
                st.success(f"✅ Exact match found: **{exact['name']}**")
                with st.container(border=True):
                    _render_report_card(exact, key_prefix="search_exact")
            else:
                if partials:
                    st.info(
                        "No exact match. Did you mean one of these?\n\n"
                        + "\n".join(f"- **{p}**" for p in partials)
                    )
                else:
                    st.error("❌ Record not found.")
