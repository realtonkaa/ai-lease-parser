"""Tests for src/fields.py — lease field definitions."""

import pytest
from src.fields import (
    LEASE_FIELDS,
    get_required_fields,
    get_all_field_names,
    get_field_type,
    get_field_description,
    is_required,
)


class TestLeaseFieldsStructure:
    """Tests for the LEASE_FIELDS dictionary structure."""

    def test_lease_fields_is_dict(self):
        assert isinstance(LEASE_FIELDS, dict)

    def test_lease_fields_not_empty(self):
        assert len(LEASE_FIELDS) > 0

    def test_all_fields_have_type(self):
        for name, info in LEASE_FIELDS.items():
            assert "type" in info, f"Field '{name}' missing 'type'"

    def test_all_fields_have_required(self):
        for name, info in LEASE_FIELDS.items():
            assert "required" in info, f"Field '{name}' missing 'required'"

    def test_all_fields_have_description(self):
        for name, info in LEASE_FIELDS.items():
            assert "description" in info, f"Field '{name}' missing 'description'"

    def test_required_is_bool(self):
        for name, info in LEASE_FIELDS.items():
            assert isinstance(info["required"], bool), f"Field '{name}' required is not bool"

    def test_valid_types(self):
        valid_types = {"string", "float", "int", "date", "list"}
        for name, info in LEASE_FIELDS.items():
            assert info["type"] in valid_types, f"Field '{name}' has invalid type: {info['type']}"

    def test_total_field_count(self):
        assert len(LEASE_FIELDS) == 13

    def test_has_tenant_name(self):
        assert "tenant_name" in LEASE_FIELDS

    def test_has_monthly_rent(self):
        assert "monthly_rent" in LEASE_FIELDS

    def test_monthly_rent_is_float(self):
        assert LEASE_FIELDS["monthly_rent"]["type"] == "float"

    def test_monthly_rent_is_required(self):
        assert LEASE_FIELDS["monthly_rent"]["required"] is True

    def test_pet_policy_is_optional(self):
        assert LEASE_FIELDS["pet_policy"]["required"] is False

    def test_utilities_type_is_list(self):
        assert LEASE_FIELDS["utilities_included"]["type"] == "list"

    def test_lease_dates_are_date_type(self):
        assert LEASE_FIELDS["lease_start_date"]["type"] == "date"
        assert LEASE_FIELDS["lease_end_date"]["type"] == "date"


class TestGetRequiredFields:
    """Tests for get_required_fields()."""

    def test_returns_list(self):
        assert isinstance(get_required_fields(), list)

    def test_returns_only_required(self):
        required = get_required_fields()
        for field in required:
            assert LEASE_FIELDS[field]["required"] is True

    def test_required_count(self):
        required = get_required_fields()
        assert len(required) == 7  # 7 required fields

    def test_tenant_name_in_required(self):
        assert "tenant_name" in get_required_fields()

    def test_landlord_name_in_required(self):
        assert "landlord_name" in get_required_fields()

    def test_property_address_in_required(self):
        assert "property_address" in get_required_fields()

    def test_monthly_rent_in_required(self):
        assert "monthly_rent" in get_required_fields()

    def test_security_deposit_in_required(self):
        assert "security_deposit" in get_required_fields()

    def test_lease_start_date_in_required(self):
        assert "lease_start_date" in get_required_fields()

    def test_lease_end_date_in_required(self):
        assert "lease_end_date" in get_required_fields()

    def test_pet_policy_not_in_required(self):
        assert "pet_policy" not in get_required_fields()


class TestGetAllFieldNames:
    """Tests for get_all_field_names()."""

    def test_returns_list(self):
        assert isinstance(get_all_field_names(), list)

    def test_length_matches_lease_fields(self):
        assert len(get_all_field_names()) == len(LEASE_FIELDS)

    def test_contains_all_fields(self):
        all_names = get_all_field_names()
        for name in LEASE_FIELDS:
            assert name in all_names


class TestHelperFunctions:
    """Tests for get_field_type, get_field_description, is_required."""

    def test_get_field_type_known_field(self):
        assert get_field_type("monthly_rent") == "float"

    def test_get_field_type_unknown_field(self):
        assert get_field_type("nonexistent_field") is None

    def test_get_field_description_known(self):
        desc = get_field_description("tenant_name")
        assert desc is not None
        assert len(desc) > 0

    def test_get_field_description_unknown(self):
        assert get_field_description("xyz") is None

    def test_is_required_true(self):
        assert is_required("monthly_rent") is True

    def test_is_required_false(self):
        assert is_required("pet_policy") is False

    def test_is_required_unknown(self):
        assert is_required("unknown_field") is False
