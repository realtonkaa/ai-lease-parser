"""Lease field definitions for structured extraction."""

LEASE_FIELDS = {
    "tenant_name": {"type": "string", "required": True, "description": "Full name of tenant(s)"},
    "landlord_name": {"type": "string", "required": True, "description": "Full name of landlord/property manager"},
    "property_address": {"type": "string", "required": True, "description": "Full street address of rental property"},
    "monthly_rent": {"type": "float", "required": True, "description": "Monthly rent amount in dollars"},
    "security_deposit": {"type": "float", "required": True, "description": "Security deposit amount"},
    "lease_start_date": {"type": "date", "required": True, "description": "Lease start date"},
    "lease_end_date": {"type": "date", "required": True, "description": "Lease end date"},
    "late_fee_amount": {"type": "float", "required": False, "description": "Late payment fee amount"},
    "late_fee_grace_period": {"type": "int", "required": False, "description": "Days before late fee applies"},
    "pet_policy": {"type": "string", "required": False, "description": "Pet policy (allowed/not allowed/deposit)"},
    "utilities_included": {"type": "list", "required": False, "description": "List of included utilities"},
    "parking": {"type": "string", "required": False, "description": "Parking arrangements"},
    "renewal_terms": {"type": "string", "required": False, "description": "Auto-renewal or month-to-month terms"},
}


def get_required_fields():
    """Return list of required field names."""
    return [k for k, v in LEASE_FIELDS.items() if v["required"]]


def get_all_field_names():
    """Return list of all field names."""
    return list(LEASE_FIELDS.keys())


def get_field_type(field_name):
    """Return the type of a given field."""
    if field_name in LEASE_FIELDS:
        return LEASE_FIELDS[field_name]["type"]
    return None


def get_field_description(field_name):
    """Return the description of a given field."""
    if field_name in LEASE_FIELDS:
        return LEASE_FIELDS[field_name]["description"]
    return None


def is_required(field_name):
    """Return True if field is required."""
    if field_name in LEASE_FIELDS:
        return LEASE_FIELDS[field_name]["required"]
    return False
