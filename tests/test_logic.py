"""
tests/test_logic.py – Unit tests for the business logic module.

Run with:  pytest tests/ -v
"""

import pytest

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


# ==================================================================
# Fixtures
# ==================================================================
@pytest.fixture
def sample_records():
    """A small set of records covering different scenarios."""
    return [
        {"name": "Photos", "users": 1, "size": 200.0, "access": "Read Only"},
        {"name": "Sales", "users": 8, "size": 2000.0, "access": "Read & Write"},
        {"name": "Logs", "users": 500, "size": 20000.0, "access": "Read & Write"},
        {"name": "Backup", "users": 1, "size": 600.0, "access": "Read Only"},
    ]


@pytest.fixture
def empty_records():
    return []


# ==================================================================
# Share Level
# ==================================================================
class TestGetShareLevel:
    @pytest.mark.parametrize(
        "users, expected",
        [
            (1, "Individual"),
            (2, "Team"),
            (5, "Team"),
            (TEAM_MAX, "Team"),           # 10
            (TEAM_MAX + 1, "Organization"),  # 11
            (50, "Organization"),
            (ORG_MAX, "Organization"),     # 100
            (ORG_MAX + 1, "Large Scale"),  # 101
            (1000, "Large Scale"),
        ],
    )
    def test_share_level(self, users, expected):
        assert get_share_level(users) == expected


# ==================================================================
# Storage Method
# ==================================================================
class TestGetStorageMethod:
    @pytest.mark.parametrize(
        "size, users, expected",
        [
            # Local Storage boundary
            (SMALL_SIZE_MB, 1, "Local Storage"),       # 500 MB, 1 user
            (SMALL_SIZE_MB + 1, 1, "Shared Storage"),  # 501 MB, 1 user -> not Local (>500), but Shared (users<=10, size<=5000)
            (100.0, 1, "Local Storage"),
            # Shared Storage boundary
            (MEDIUM_SIZE_MB, TEAM_MAX, "Shared Storage"),     # 5000 MB, 10 users
            (MEDIUM_SIZE_MB + 1, TEAM_MAX, "Cloud Storage"),  # 5001 MB, 10 users
            (100.0, TEAM_MAX, "Shared Storage"),
            # Cloud Storage
            (100.0, TEAM_MAX + 1, "Cloud Storage"),    # 11 users
            (100.0, 200, "Cloud Storage"),
        ],
    )
    def test_storage_method(self, size, users, expected):
        assert get_storage_method(size, users) == expected

    def test_single_user_above_small_below_medium(self):
        """1 user, 501 MB: fails the 'users==1 and size<=500' rule,
        but passes 'users<=10 and size<=5000' → Shared Storage."""
        assert get_storage_method(501, 1) == "Shared Storage"


# ==================================================================
# Build Report
# ==================================================================
class TestBuildReport:
    def test_report_keys(self, sample_records):
        report = build_report(sample_records[0])
        expected_keys = {
            "Data Name",
            "Size (MB)",
            "Number of Users",
            "Access Type",
            "Share Level",
            "Suggested Storage Method",
        }
        assert set(report.keys()) == expected_keys

    def test_report_values(self):
        rec = {"name": "Test", "users": 1, "size": 100.0, "access": "Read Only"}
        report = build_report(rec)
        assert report["Data Name"] == "Test"
        assert report["Share Level"] == "Individual"
        assert report["Suggested Storage Method"] == "Local Storage"


# ==================================================================
# Warnings
# ==================================================================
class TestNeedsWarning:
    def test_rw_multiple_users(self):
        rec = {"name": "X", "users": 5, "size": 100, "access": "Read & Write"}
        assert needs_warning(rec) is True

    def test_rw_single_user(self):
        rec = {"name": "X", "users": 1, "size": 100, "access": "Read & Write"}
        assert needs_warning(rec) is False

    def test_readonly_multiple_users(self):
        rec = {"name": "X", "users": 5, "size": 100, "access": "Read Only"}
        assert needs_warning(rec) is False

    def test_readonly_single_user(self):
        rec = {"name": "X", "users": 1, "size": 100, "access": "Read Only"}
        assert needs_warning(rec) is False


# ==================================================================
# Total Size
# ==================================================================
class TestTotalSize:
    def test_with_records(self, sample_records):
        expected = 200.0 + 2000.0 + 20000.0 + 600.0
        assert total_size(sample_records) == pytest.approx(expected)

    def test_empty_list(self, empty_records):
        assert total_size(empty_records) == 0.0


# ==================================================================
# Largest Record
# ==================================================================
class TestLargestRecord:
    def test_with_records(self, sample_records):
        result = largest_record(sample_records)
        assert result is not None
        assert result["name"] == "Logs"
        assert result["size"] == 20000.0

    def test_empty_list(self, empty_records):
        assert largest_record(empty_records) is None


# ==================================================================
# Search
# ==================================================================
class TestSearchByName:
    def test_exact_match_case_insensitive(self, sample_records):
        exact, partials = search_by_name(sample_records, "photos")
        assert exact is not None
        assert exact["name"] == "Photos"

    def test_exact_match_upper(self, sample_records):
        exact, _ = search_by_name(sample_records, "SALES")
        assert exact is not None
        assert exact["name"] == "Sales"

    def test_partial_match(self, sample_records):
        # Searching "log" should match "Logs" exactly... let's search "lo"
        exact, partials = search_by_name(sample_records, "lo")
        # "lo" is not an exact match for any name
        assert exact is None
        # "Logs" contains "lo"
        assert "Logs" in partials

    def test_not_found(self, sample_records):
        exact, partials = search_by_name(sample_records, "nonexistent")
        assert exact is None
        assert partials == []

    def test_empty_query(self, sample_records):
        exact, partials = search_by_name(sample_records, "   ")
        assert exact is None
        assert partials == []

    def test_empty_records(self, empty_records):
        exact, partials = search_by_name(empty_records, "anything")
        assert exact is None
        assert partials == []
