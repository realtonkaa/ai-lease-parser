"""Tests for src/extractor.py — regex-based field extraction."""

import pytest
from src.extractor import (
    extract_with_regex,
    extract,
    get_values,
    get_confidence_scores,
    merge_results,
    _clean_amount,
    _parse_utilities,
)


class TestCleanAmount:
    """Unit tests for _clean_amount helper."""

    def test_simple_number(self):
        assert _clean_amount("1450") == 1450.0

    def test_number_with_cents(self):
        assert _clean_amount("1450.00") == 1450.0

    def test_number_with_comma(self):
        assert _clean_amount("2,100.00") == 2100.0

    def test_invalid_returns_none(self):
        assert _clean_amount("not a number") is None

    def test_empty_returns_none(self):
        assert _clean_amount("") is None

    def test_none_returns_none(self):
        assert _clean_amount(None) is None


class TestParseUtilities:
    """Unit tests for _parse_utilities helper."""

    def test_comma_separated(self):
        result = _parse_utilities("water, electricity, gas")
        assert "water" in result
        assert "electricity" in result
        assert "gas" in result

    def test_and_separated(self):
        result = _parse_utilities("water and trash collection")
        assert len(result) == 2

    def test_single_utility(self):
        result = _parse_utilities("water")
        assert result == ["water"]

    def test_empty_string(self):
        result = _parse_utilities("")
        assert result == []


class TestExtractWithRegexLease1:
    """Extraction tests on sample_lease_1.txt format."""

    def test_extracts_monthly_rent(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["monthly_rent"]["value"] == 1450.0

    def test_extracts_security_deposit(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["security_deposit"]["value"] == 2900.0

    def test_extracts_late_fee(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["late_fee_amount"]["value"] == 75.0

    def test_extracts_late_fee_grace_period(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["late_fee_grace_period"]["value"] == 5

    def test_extracts_tenant_name(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["tenant_name"]["value"] is not None
        assert "Garcia" in results["tenant_name"]["value"]

    def test_extracts_landlord_name(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["landlord_name"]["value"] is not None
        assert "Henderson" in results["landlord_name"]["value"]

    def test_extracts_property_address(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["property_address"]["value"] is not None
        assert "742" in results["property_address"]["value"]

    def test_extracts_pet_policy(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["pet_policy"]["value"] is not None
        assert "allowed" in results["pet_policy"]["value"].lower()

    def test_extracts_utilities(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["utilities_included"]["value"] is not None

    def test_extracts_parking(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["parking"]["value"] is not None

    def test_confidence_for_found_fields(self, lease1_text):
        results = extract_with_regex(lease1_text)
        assert results["monthly_rent"]["confidence"] > 0
        assert results["security_deposit"]["confidence"] > 0

    def test_confidence_zero_for_missing_fields(self):
        results = extract_with_regex("No lease fields here at all.")
        assert results["monthly_rent"]["confidence"] == 0.0

    def test_extracts_start_date(self, lease1_text):
        results = extract_with_regex(lease1_text)
        val = results["lease_start_date"]["value"]
        assert val is not None
        assert "2026" in val or "January" in val or "01" in str(val)

    def test_extracts_end_date(self, lease1_text):
        results = extract_with_regex(lease1_text)
        val = results["lease_end_date"]["value"]
        assert val is not None
        assert "2026" in str(val)


class TestExtractWithRegexLease2:
    """Extraction tests on sample_lease_2.txt format."""

    def test_extracts_monthly_rent(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["monthly_rent"]["value"] == 2100.0

    def test_extracts_security_deposit(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["security_deposit"]["value"] == 2100.0

    def test_extracts_late_fee(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["late_fee_amount"]["value"] == 100.0

    def test_extracts_landlord_name(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["landlord_name"]["value"] is not None
        assert "Greenfield" in results["landlord_name"]["value"]

    def test_extracts_property_address(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["property_address"]["value"] is not None
        assert "1500" in results["property_address"]["value"]

    def test_extracts_pet_policy(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["pet_policy"]["value"] is not None

    def test_extracts_utilities(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["utilities_included"]["value"] is not None

    def test_extracts_parking(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["parking"]["value"] is not None

    def test_extracts_grace_period(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["late_fee_grace_period"]["value"] == 3

    def test_extracts_renewal_terms(self, lease2_text):
        results = extract_with_regex(lease2_text)
        assert results["renewal_terms"]["value"] is not None


class TestExtractEdgeCases:
    """Edge cases for extraction."""

    def test_empty_text_returns_all_none(self):
        results = extract_with_regex("")
        for field, entry in results.items():
            assert entry["value"] is None

    def test_partial_text_returns_partial_results(self):
        text = "Monthly Rent: $1,200.00"
        results = extract_with_regex(text)
        assert results["monthly_rent"]["value"] == 1200.0
        assert results["security_deposit"]["value"] is None

    def test_malformed_amount_returns_none(self):
        text = "Rent: $abc.def"
        results = extract_with_regex(text)
        assert results["monthly_rent"]["value"] is None

    def test_zero_confidence_when_not_found(self):
        results = extract_with_regex("Nothing to find here.")
        for field, entry in results.items():
            assert entry["confidence"] == 0.0


class TestGetValuesAndScores:
    """Tests for get_values and get_confidence_scores helpers."""

    def test_get_values_flattens(self, lease1_text):
        results = extract_with_regex(lease1_text)
        values = get_values(results)
        assert isinstance(values, dict)
        assert "monthly_rent" in values
        assert values["monthly_rent"] == 1450.0

    def test_get_confidence_scores(self, lease1_text):
        results = extract_with_regex(lease1_text)
        scores = get_confidence_scores(results)
        assert isinstance(scores, dict)
        assert scores["monthly_rent"] > 0.0

    def test_get_values_none_for_missing(self):
        results = extract_with_regex("Nothing here.")
        values = get_values(results)
        assert values["monthly_rent"] is None


class TestMergeResults:
    """Tests for merge_results."""

    def test_llm_takes_priority(self):
        from src.fields import get_all_field_names
        r = {f: {"value": None, "confidence": 0.0} for f in get_all_field_names()}
        l = {f: {"value": None, "confidence": 0.0} for f in get_all_field_names()}
        r["monthly_rent"] = {"value": 1000.0, "confidence": 0.8}
        l["monthly_rent"] = {"value": 1500.0, "confidence": 0.9}
        merged = merge_results(r, l)
        assert merged["monthly_rent"]["value"] == 1500.0

    def test_regex_used_when_llm_low_confidence(self):
        regex = {"monthly_rent": {"value": 1500.0, "confidence": 0.8}}
        llm = {"monthly_rent": {"value": None, "confidence": 0.1}}
        # Need all fields in both dicts for merge
        from src.fields import get_all_field_names
        r = {f: {"value": None, "confidence": 0.0} for f in get_all_field_names()}
        l = {f: {"value": None, "confidence": 0.0} for f in get_all_field_names()}
        r["monthly_rent"] = {"value": 1500.0, "confidence": 0.8}
        l["monthly_rent"] = {"value": None, "confidence": 0.1}
        merged = merge_results(r, l)
        assert merged["monthly_rent"]["value"] == 1500.0


class TestExtractFunction:
    """Tests for the main extract() function."""

    def test_extract_without_llm(self, lease1_text):
        results = extract(lease1_text, use_llm=False)
        values = get_values(results)
        assert values["monthly_rent"] == 1450.0

    def test_extract_returns_all_fields(self, lease1_text):
        from src.fields import get_all_field_names
        results = extract(lease1_text, use_llm=False)
        for field in get_all_field_names():
            assert field in results
