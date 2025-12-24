"""Validate extracted lease data for correctness and completeness."""

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from .fields import get_required_fields
from .config import get_config


# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

DATE_FORMATS = [
    "%B %d, %Y",    # January 1, 2026
    "%B %d %Y",     # January 1 2026
    "%b %d, %Y",    # Jan 1, 2026
    "%b %d %Y",     # Jan 1 2026
    "%m/%d/%Y",     # 01/01/2026
    "%Y-%m-%d",     # 2026-01-01
    "%d-%m-%Y",     # 01-01-2026
    "%m-%d-%Y",     # 01-01-2026
    "%B %d, %Y".replace(",", ""),  # duplicate safe
]


def parse_date(value: Any) -> Optional[date]:
    """
    Try to parse a date from various formats.
    Accepts date objects, datetime objects, or strings.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        return None

    value = value.strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------------
# Individual field validators
# ---------------------------------------------------------------------------

def validate_date_field(value: Any, field_name: str) -> Tuple[bool, Optional[str]]:
    """Validate a date field. Returns (is_valid, warning_message)."""
    if value is None:
        return False, f"{field_name} is missing"

    parsed = parse_date(value)
    if parsed is None:
        return False, f"{field_name} could not be parsed as a date: '{value}'"

    return True, None


def validate_date_range(start_value: Any, end_value: Any) -> Tuple[bool, Optional[str]]:
    """Validate that end date is after start date."""
    start = parse_date(start_value)
    end = parse_date(end_value)

    if start is None or end is None:
        return True, None  # Already reported as individual errors

    if end <= start:
        return False, (
            f"lease_end_date ({end}) must be after lease_start_date ({start})"
        )

    return True, None


def validate_rent(value: Any) -> Tuple[bool, Optional[str]]:
    """Validate monthly rent is within a reasonable range."""
    if value is None:
        return False, "monthly_rent is missing"

    try:
        amount = float(value)
    except (TypeError, ValueError):
        return False, f"monthly_rent is not a valid number: '{value}'"

    rent_min = get_config("rent_min", 100.0)
    rent_max = get_config("rent_max", 50000.0)

    if amount < rent_min:
        return False, f"monthly_rent ${amount:.2f} seems too low (minimum ${rent_min:.2f})"
    if amount > rent_max:
        return False, f"monthly_rent ${amount:.2f} seems too high (maximum ${rent_max:.2f})"

    return True, None


def validate_deposit(deposit_value: Any, rent_value: Any) -> Tuple[bool, Optional[str]]:
    """Validate security deposit is within a reasonable range."""
    if deposit_value is None:
        return False, "security_deposit is missing"

    try:
        deposit = float(deposit_value)
    except (TypeError, ValueError):
        return False, f"security_deposit is not a valid number: '{deposit_value}'"

    if deposit < 0:
        return False, f"security_deposit ${deposit:.2f} cannot be negative"

    if rent_value is not None:
        try:
            rent = float(rent_value)
            multiplier = get_config("deposit_max_multiplier", 3.0)
            if rent > 0 and deposit > rent * multiplier:
                return (
                    False,
                    f"security_deposit ${deposit:.2f} is more than {multiplier}x rent "
                    f"(${rent:.2f}), which is unusually high",
                )
        except (TypeError, ValueError):
            pass

    return True, None


def validate_required_fields(values: Dict[str, Any]) -> List[str]:
    """
    Check that all required fields are present and non-None.
    Returns a list of missing field names.
    """
    required = get_required_fields()
    missing = [f for f in required if values.get(f) is None]
    return missing


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------

def validate(values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a dict of extracted lease field values.

    Args:
        values: Dict mapping field_name -> extracted value.

    Returns:
        Dict with keys:
          - "is_valid": bool — True if no errors
          - "errors": List[str] — blocking issues
          - "warnings": List[str] — non-blocking concerns
          - "missing_required": List[str] — required fields not found
    """
    errors = []
    warnings = []

    # Check required fields
    missing = validate_required_fields(values)
    for field in missing:
        errors.append(f"Required field '{field}' is missing")

    # Validate dates
    for date_field in ("lease_start_date", "lease_end_date"):
        val = values.get(date_field)
        if val is not None:
            ok, msg = validate_date_field(val, date_field)
            if not ok:
                errors.append(msg)

    # Validate date range
    ok, msg = validate_date_range(
        values.get("lease_start_date"), values.get("lease_end_date")
    )
    if not ok:
        errors.append(msg)

    # Validate rent
    rent_val = values.get("monthly_rent")
    if rent_val is not None:
        ok, msg = validate_rent(rent_val)
        if not ok:
            errors.append(msg)

    # Validate deposit
    deposit_val = values.get("security_deposit")
    if deposit_val is not None:
        ok, msg = validate_deposit(deposit_val, rent_val)
        if not ok:
            warnings.append(msg)  # High deposit is a warning, not hard error

    # Optional field warnings
    optional_missing = [
        f for f in ("late_fee_amount", "pet_policy", "renewal_terms", "parking")
        if values.get(f) is None
    ]
    if optional_missing:
        warnings.append(
            f"Optional fields not found: {', '.join(optional_missing)}"
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "missing_required": missing,
    }
