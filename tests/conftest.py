"""Shared pytest fixtures."""

import os
from pathlib import Path
import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def lease1_path():
    """Path to sample_lease_1.txt"""
    return FIXTURES_DIR / "sample_lease_1.txt"


@pytest.fixture
def lease2_path():
    """Path to sample_lease_2.txt"""
    return FIXTURES_DIR / "sample_lease_2.txt"


@pytest.fixture
def lease1_text(lease1_path):
    """Full text content of sample_lease_1.txt"""
    return lease1_path.read_text(encoding="utf-8")


@pytest.fixture
def lease2_text(lease2_path):
    """Full text content of sample_lease_2.txt"""
    return lease2_path.read_text(encoding="utf-8")


@pytest.fixture
def minimal_valid_values():
    """Minimal dict with all required fields populated."""
    return {
        "tenant_name": "John Doe",
        "landlord_name": "Jane Smith",
        "property_address": "123 Main St, Anytown, CA 90210",
        "monthly_rent": 1500.0,
        "security_deposit": 3000.0,
        "lease_start_date": "January 1, 2026",
        "lease_end_date": "December 31, 2026",
        "late_fee_amount": None,
        "late_fee_grace_period": None,
        "pet_policy": None,
        "utilities_included": None,
        "parking": None,
        "renewal_terms": None,
    }


@pytest.fixture
def full_values():
    """Full dict with all fields populated (from sample_lease_1)."""
    return {
        "tenant_name": "Maria Garcia",
        "landlord_name": "Robert J. Henderson",
        "property_address": "742 Evergreen Terrace, Apt 3B, Springfield, IL 62704",
        "monthly_rent": 1450.0,
        "security_deposit": 2900.0,
        "lease_start_date": "January 1, 2026",
        "lease_end_date": "December 31, 2026",
        "late_fee_amount": 75.0,
        "late_fee_grace_period": 5,
        "pet_policy": "Pets are allowed with a $500 pet deposit. Maximum 2 pets, no aggressive breeds.",
        "utilities_included": ["water", "trash collection"],
        "parking": "One assigned parking space included (Space #14).",
        "renewal_terms": "This lease shall automatically renew on a month-to-month basis unless either party gives 30 days written notice.",
    }


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary directory for output files."""
    return tmp_path
