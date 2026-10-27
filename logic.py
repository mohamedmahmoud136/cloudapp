"""
logic.py – Pure-Python business logic for the Data Storage & Sharing System.

This module contains NO Streamlit imports so that every function
can be unit-tested independently.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ------------------------------------------------------------------
# CONSTANTS – easy to edit in one place
# ------------------------------------------------------------------
TEAM_MAX: int = 10            # max users for "Team"
ORG_MAX: int = 100            # max users for "Organization"
SMALL_SIZE_MB: float = 500    # max size (MB) for Local Storage
MEDIUM_SIZE_MB: float = 5000  # max size (MB) for Shared Storage


# ------------------------------------------------------------------
# Type alias for a record stored in session_state
# ------------------------------------------------------------------
RecordDict = Dict[str, object]
# {"name": str, "users": int, "size": float, "access": str}


# ------------------------------------------------------------------
# FEATURE 2 – Share Level
# ------------------------------------------------------------------
def get_share_level(users: int) -> str:
    """Return the share level for a given number of users.

    Rules
    -----
    - users == 1            → "Individual"
    - users <= TEAM_MAX     → "Team"
    - users <= ORG_MAX      → "Organization"
    - otherwise             → "Large Scale"
    """
    if users == 1:
        return "Individual"
    if users <= TEAM_MAX:
        return "Team"
    if users <= ORG_MAX:
        return "Organization"
    return "Large Scale"


# ------------------------------------------------------------------
# FEATURE 3 – Storage Method
# ------------------------------------------------------------------
def get_storage_method(size_mb: float, users: int) -> str:
    """Suggest a storage method based on data size and number of users.

    Rules
    -----
    - users == 1  AND  size_mb <= SMALL_SIZE_MB   → "Local Storage"
    - users <= TEAM_MAX  AND  size_mb <= MEDIUM_SIZE_MB  → "Shared Storage"
    - otherwise                                    → "Cloud Storage"
    """
    if users == 1 and size_mb <= SMALL_SIZE_MB:
        return "Local Storage"
    if users <= TEAM_MAX and size_mb <= MEDIUM_SIZE_MB:
        return "Shared Storage"
    return "Cloud Storage"


# ------------------------------------------------------------------
# FEATURE 4 – Report builder
# ------------------------------------------------------------------
def build_report(record: RecordDict) -> Dict[str, str]:
    """Build a human-readable report dictionary for a single record.

    Parameters
    ----------
    record : dict
        Must contain keys ``name``, ``users``, ``size``, ``access``.

    Returns
    -------
    dict
        Keys are human-readable labels; values are display strings.
    """
    share_level = get_share_level(record["users"])
    storage_method = get_storage_method(record["size"], record["users"])

    return {
        "Data Name": record["name"],
        "Size (MB)": f"{record['size']:.2f}",
        "Number of Users": str(record["users"]),
        "Access Type": record["access"],
        "Share Level": share_level,
        "Suggested Storage Method": storage_method,
    }


# ------------------------------------------------------------------
# FEATURE 5 – Warning check
# ------------------------------------------------------------------
def needs_warning(record: RecordDict) -> bool:
    """Return True if the record should display a write-access warning.

    A warning is needed when *access* is ``"Read & Write"`` **and**
    more than one user is involved.
    """
    return record["access"] == "Read & Write" and record["users"] > 1


# ------------------------------------------------------------------
# FEATURE 6 – Statistics helpers
# ------------------------------------------------------------------
def total_size(records: List[RecordDict]) -> float:
    """Return the sum of all record sizes (MB).  Returns 0.0 for an empty list."""
    if not records:
        return 0.0
    return sum(r["size"] for r in records)


def largest_record(records: List[RecordDict]) -> Optional[RecordDict]:
    """Return the record with the biggest size, or ``None`` for an empty list."""
    if not records:
        return None
    return max(records, key=lambda r: r["size"])


def search_by_name(
    records: List[RecordDict], name: str
) -> Tuple[Optional[RecordDict], List[str]]:
    """Search records by name (case-insensitive).

    Returns
    -------
    (exact_match_or_None, list_of_partial_match_names)

    The partial-match list contains record names that *contain* the
    search term as a substring but are not the exact match.
    """
    query = name.strip().lower()
    if not query:
        return None, []

    exact: Optional[RecordDict] = None
    partials: List[str] = []

    for r in records:
        r_lower = r["name"].lower()
        if r_lower == query:
            exact = r
        elif query in r_lower:
            partials.append(r["name"])

    return exact, partials
