"""Tests for src/validator.py — data validation."""

import pytest
from datetime import date

from src.validator import (
    validate,
    validate_rent,
    validate_deposit,
    validate_date_field,
    validate_date_range,
    validate_required_fields,
    parse_date,
)


class TestParseDate:
    """Tests for the parse_date utility."""

    def test_parse_iso_format(self):
        d = parse_date("2026-01-01")
        assert d == date(2026, 1, 1)

    def test_parse_long_format(self):
        d = parse_date("January 1, 2026")
        assert d == date(2026, 1, 1)

    def test_parse_short_month(self):
        d = parse_date("Jan 1, 2026")
        assert d == date(2026, 1, 1)

    def test_parse_slash_format(self):
        d = parse_date("01/01/2026")
        assert d == date(2026, 1, 1)

    def test_parse_date_object(self):
        d = parse_date(date(2026, 1, 1))
        assert d == date(2026, 1, 1)

    def test_parse_none_returns_none(self):
        assert parse_date(None) is None

    def test_parse_invalid_string_returns_none(self):
        assert parse_date("not a date") is None

    def test_parse_december(self):
        d = parse_date("December 31, 2026")
        assert d == date(2026, 12, 31)

    def test_parse_february(self):
        d = parse_date("February 1, 2026")
        assert d == date(2026, 2, 1)


class TestValidateDateField:
    """Tests for validate_date_field()."""

    def test_valid_date_string(self):
        ok, msg = validate_date_field("January 1, 2026", "lease_start_date")
        assert ok is True
        assert msg is None

    def test_none_value_fails(self):
        ok, msg = validate_date_field(None, "lease_start_date")
        assert ok is False
        assert msg is not None

    def test_invalid_date_string_fails(self):
        ok, msg = validate_date_field("not-a-date", "lease_start_date")
        assert ok is False

    def test_iso_date_valid(self):
        ok, msg = validate_date_field("2026-01-01", "lease_start_date")
        assert ok is True


class TestValidateDateRange:
    """Tests for validate_date_range()."""

    def test_valid_range(self):
        ok, msg = validate_date_range("January 1, 2026", "December 31, 2026")
        assert ok is True
        assert msg is None

    def test_end_before_start_fails(self):
        ok, msg = validate_date_range("December 31, 2026", "January 1, 2026")
        assert ok is False
        assert msg is not None

    def test_same_date_fails(self):
        ok, msg = validate_date_range("January 1, 2026", "January 1, 2026")
        assert ok is False

    def test_none_start_passes(self):
        ok, msg = validate_date_range(None, "December 31, 2026")
        assert ok is True  # Individual field validation handles None

    def test_none_end_passes(self):
        ok, msg = validate_date_range("January 1, 2026", None)
        assert ok is True

    def test_cross_year_range(self):
        ok, msg = validate_date_range("February 1, 2026", "January 31, 2027")
        assert ok is True


class TestValidateRent:
    """Tests for validate_rent()."""

    def test_normal_rent_passes(self):
        ok, msg = validate_rent(1500.0)
        assert ok is True

    def test_rent_too_low_fails(self):
        ok, msg = validate_rent(50.0)
        assert ok is False

    def test_rent_too_high_fails(self):
        ok, msg = validate_rent(60000.0)
        assert ok is False

    def test_none_rent_fails(self):
        ok, msg = validate_rent(None)
        assert ok is False

    def test_minimum_boundary(self):
        ok, msg = validate_rent(100.0)
        assert ok is True

    def test_maximum_boundary(self):
        ok, msg = validate_rent(50000.0)
        assert ok is True

    def test_string_number_passes(self):
        ok, msg = validate_rent("1500")
        assert ok is True

    def test_invalid_string_fails(self):
        ok, msg = validate_rent("not-a-number")
        assert ok is False


class TestValidateDeposit:
    """Tests for validate_deposit()."""

    def test_normal_deposit_passes(self):
        ok, msg = validate_deposit(3000.0, 1500.0)
        assert ok is True

    def test_none_deposit_fails(self):
        ok, msg = validate_deposit(None, 1500.0)
        assert ok is False

    def test_negative_deposit_fails(self):
        ok, msg = validate_deposit(-100.0, 1500.0)
        assert ok is False

    def test_deposit_exceeds_3x_rent_warns(self):
        ok, msg = validate_deposit(6000.0, 1500.0)
        assert ok is False  # Returns False with warning message
        assert msg is not None

    def test_deposit_equals_rent_passes(self):
        ok, msg = validate_deposit(1500.0, 1500.0)
        assert ok is True

    def test_zero_deposit_passes(self):
        ok, msg = validate_deposit(0.0, 1500.0)
        assert ok is True

    def test_deposit_without_rent_passes(self):
        ok, msg = validate_deposit(3000.0, None)
        assert ok is True


class TestValidateRequiredFields:
    """Tests for validate_required_fields()."""

    def test_all_present_returns_empty_list(self, minimal_valid_values):
        missing = validate_required_fields(minimal_valid_values)
        assert missing == []

    def test_missing_tenant_name(self, minimal_valid_values):
        minimal_valid_values["tenant_name"] = None
        missing = validate_required_fields(minimal_valid_values)
        assert "tenant_name" in missing

    def test_missing_rent(self, minimal_valid_values):
        minimal_valid_values["monthly_rent"] = None
        missing = validate_required_fields(minimal_valid_values)
        assert "monthly_rent" in missing

    def test_all_missing(self):
        missing = validate_required_fields({})
        from src.fields import get_required_fields
        assert set(missing) == set(get_required_fields())


class TestValidateMain:
    """Tests for the main validate() function."""

    def test_valid_lease_passes(self, minimal_valid_values):
        result = validate(minimal_valid_values)
        assert result["is_valid"] is True
        assert result["errors"] == []

    def test_missing_required_field_fails(self, minimal_valid_values):
        minimal_valid_values["tenant_name"] = None
        result = validate(minimal_valid_values)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_invalid_date_range_fails(self, minimal_valid_values):
        minimal_valid_values["lease_start_date"] = "December 31, 2026"
        minimal_valid_values["lease_end_date"] = "January 1, 2026"
        result = validate(minimal_valid_values)
        assert result["is_valid"] is False

    def test_low_rent_fails(self, minimal_valid_values):
        minimal_valid_values["monthly_rent"] = 10.0
        result = validate(minimal_valid_values)
        assert result["is_valid"] is False

    def test_result_has_required_keys(self, minimal_valid_values):
        result = validate(minimal_valid_values)
        assert "is_valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "missing_required" in result

    def test_warnings_for_optional_fields(self, minimal_valid_values):
        result = validate(minimal_valid_values)
        assert len(result["warnings"]) > 0  # optional fields not found

    def test_full_valid_lease(self, full_values):
        result = validate(full_values)
        assert result["is_valid"] is True

    def test_missing_required_list(self, minimal_valid_values):
        minimal_valid_values["monthly_rent"] = None
        minimal_valid_values["security_deposit"] = None
        result = validate(minimal_valid_values)
        assert "monthly_rent" in result["missing_required"]
        assert "security_deposit" in result["missing_required"]
