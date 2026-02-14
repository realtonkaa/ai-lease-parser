"""Extract structured lease fields using regex and optional LLM."""

import re
import json
from typing import Any, Dict, Optional, Tuple

from .fields import LEASE_FIELDS, get_all_field_names
from .config import get_openai_api_key, get_config


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

PATTERNS = {
    "monthly_rent": [
        r"(?:monthly\s+rent(?:al)?(?:\s+amount)?|rent\s+amount|rent)[:\s]+\$?([\d,]+\.?\d*)",
        r"(?:monthly\s+rental\s+amount)[:\s]+\$?([\d,]+\.?\d*)",
        r"pay\s+(?:monthly\s+)?rent\s+of\s+\$?([\d,]+\.?\d*)",
    ],
    "security_deposit": [
        r"(?:security\s+deposit(?:\s+amount)?|deposit\s+amount)[:\s]+\$?([\d,]+\.?\d*)",
        r"deposited\s+\$?([\d,]+\.?\d*)\s+as\s+a\s+security",
    ],
    "lease_start_date": [
        r"(?:commence\s+on|start(?:ing)?\s+(?:date)?|begin(?:ning)?\s+(?:date)?)[:\s]*([\w]+\s+\d{1,2},?\s+\d{4})",
        r"(?:Beginning\s+Date)[:\s]*([\w]+\s+\d{1,2},?\s+\d{4})",
        r"(?:commence\s+on|start\s+on)[:\s]*([\w\s,]+\d{4})",
    ],
    "lease_end_date": [
        r"(?:terminate\s+on|end(?:ing)?\s+(?:date)?|expir(?:e|es|ation)\s+(?:date)?)[:\s]*([\w]+\s+\d{1,2},?\s+\d{4})",
        r"(?:Ending\s+Date)[:\s]*([\w]+\s+\d{1,2},?\s+\d{4})",
    ],
    "tenant_name": [
        r"(?:Tenant|Lessee|Renter)\s*(?:\(Renter\))?\s*:\s*([A-Z][a-zA-Z.\-']+(?:\s+[A-Z][a-zA-Z.\-']+){1,4})",
        r"(?:Tenant|Lessee|Renter)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*[a-z]+)*(?:\s+and\s+[A-Z][a-z]+(?:\s+[A-Z]\.?\s*[a-z]+)*)?)",
    ],
    "landlord_name": [
        r"(?:Landlord|Lessor|Owner|Property\s+Manager)\s*(?:\(Owner\))?\s*:\s*(.+?)(?:\n|$)",
        r"(?:Landlord|Lessor)\s*:\s*(.+?)(?:\n|$)",
    ],
    "property_address": [
        r"(?:property\s+located\s+at|premises(?:\s+located\s+at)?|located\s+at|Property\s+Address)[:\s]*(.+?)(?:\n|$)",
        r"(?:Address)[:\s]*(\d+.+?)(?:\n|$)",
    ],
    "late_fee_amount": [
        r"(?:late\s+(?:fee|charge|payment\s+fee))[:\s]*\$?([\d,]+\.?\d*)",
        r"late\s+fee\s+of\s+\$?([\d,]+\.?\d*)",
    ],
    "late_fee_grace_period": [
        r"(?:within|after)\s+(\d+)\s+days?\s+(?:of\s+(?:the\s+)?due\s+date|grace\s+period)",
        r"(\d+)[- ]day\s+grace\s+period",
        r"assessed\s+after\s+(\d+)[- ]day\s+grace",
    ],
    "pet_policy": [
        r"(?:PET\s+(?:POLICY|CLAUSE))[:\s]*(.+?)(?:\n|$)",
        r"(?:pet\s+(?:policy|clause))[:\s]*(.+?)(?:\n|$)",
    ],
    "utilities_included": [
        r"(?:INCLUDED\s+SERVICES|utilities?\s+included|Landlord\s+shall\s+provide)[:\s]*(.+?)(?:\n|$)",
        r"(?:included\s+in\s+rent)[:\s]*(.+?)(?:\n|$)",
    ],
    "parking": [
        r"(?:VEHICLE\s+PARKING|PARKING)[:\s]*(.+?)(?:\n|$)",
        r"(?:parking\s+space)[:\s]*(.+?)(?:\n|$)",
    ],
    "renewal_terms": [
        r"(?:TERM\s+RENEWAL|RENEWAL)[:\s]*(.+?)(?:\n|$)",
        r"(?:automatically\s+renew|month-to-month)[^\n]*",
        r"(?:lease\s+converts\s+to)[^\n]*",
    ],
}


def _clean_amount(value: str) -> Optional[float]:
    """Parse a dollar amount string to float."""
    try:
        cleaned = value.replace(",", "").strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _parse_utilities(text: str) -> list:
    """Split a utilities string into a list."""
    # Common separators: comma, "and", semicolon
    parts = re.split(r",|\band\b|;", text, flags=re.IGNORECASE)
    result = []
    for part in parts:
        item = part.strip().rstrip(".")
        if item:
            result.append(item)
    return result


def extract_with_regex(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract lease fields from text using regex patterns.

    Returns:
        Dict mapping field_name -> {"value": ..., "confidence": float}
    """
    results = {}

    for field, pattern_list in PATTERNS.items():
        found = False
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                raw = match.group(1).strip()
                field_type = LEASE_FIELDS.get(field, {}).get("type", "string")

                if field_type == "float":
                    value = _clean_amount(raw)
                    if value is None:
                        continue
                elif field_type == "int":
                    try:
                        value = int(raw)
                    except ValueError:
                        continue
                elif field_type == "list":
                    value = _parse_utilities(raw)
                else:
                    value = raw

                results[field] = {"value": value, "confidence": 0.8}
                found = True
                break

        if not found:
            results[field] = {"value": None, "confidence": 0.0}

    return results


def extract_with_llm(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract lease fields using OpenAI LLM.

    Returns:
        Dict mapping field_name -> {"value": ..., "confidence": float}
    """
    api_key = get_openai_api_key()
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it to use LLM extraction."
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package is required. Install with: pip install openai")

    client = OpenAI(api_key=api_key)
    model = get_config("openai_model", "gpt-4o-mini")
    max_tokens = get_config("max_tokens", 2000)

    field_descriptions = {
        name: info["description"] for name, info in LEASE_FIELDS.items()
    }

    prompt = f"""Extract the following fields from the lease agreement text below.
Return a JSON object where each key is a field name and the value is an object with:
  - "value": the extracted value (null if not found)
  - "confidence": a float 0.0-1.0 indicating confidence

Fields to extract:
{json.dumps(field_descriptions, indent=2)}

For dates, use ISO format: YYYY-MM-DD
For monetary amounts, return as numbers (no $ sign)
For utilities_included, return a list of strings
For integer fields, return an integer

Lease text:
{text[:6000]}

Return ONLY valid JSON, no markdown, no explanation."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0,
    )

    raw_json = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    raw_json = re.sub(r"^```(?:json)?\n?", "", raw_json)
    raw_json = re.sub(r"\n?```$", "", raw_json)

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw response: {raw_json}")

    results = {}
    for field in get_all_field_names():
        if field in parsed:
            entry = parsed[field]
            if isinstance(entry, dict):
                results[field] = {
                    "value": entry.get("value"),
                    "confidence": float(entry.get("confidence", 0.9)),
                }
            else:
                results[field] = {"value": entry, "confidence": 0.9}
        else:
            results[field] = {"value": None, "confidence": 0.0}

    return results


def merge_results(
    regex_results: Dict[str, Dict[str, Any]],
    llm_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Merge regex and LLM results, preferring higher-confidence values.
    LLM results take priority when confidence >= 0.7.
    """
    merged = {}
    for field in get_all_field_names():
        regex_entry = regex_results.get(field, {"value": None, "confidence": 0.0})
        llm_entry = llm_results.get(field, {"value": None, "confidence": 0.0})

        if llm_entry["value"] is not None and llm_entry["confidence"] >= 0.7:
            merged[field] = llm_entry
        elif regex_entry["value"] is not None:
            merged[field] = regex_entry
        else:
            merged[field] = {"value": None, "confidence": 0.0}

    return merged


def extract(text: str, use_llm: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Main extraction function. Uses regex by default, optionally merges with LLM.

    Args:
        text: Full lease text.
        use_llm: If True and OPENAI_API_KEY is set, also use LLM extraction.

    Returns:
        Dict mapping field_name -> {"value": ..., "confidence": float}
    """
    regex_results = extract_with_regex(text)

    if use_llm and get_openai_api_key():
        llm_results = extract_with_llm(text)
        return merge_results(regex_results, llm_results)

    return regex_results


def get_values(extraction_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Flatten extraction results to a simple {field: value} dict."""
    return {field: entry["value"] for field, entry in extraction_results.items()}


def get_confidence_scores(extraction_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Return {field: confidence} dict from extraction results."""
    return {field: entry["confidence"] for field, entry in extraction_results.items()}


# LLM extraction is implemented in extract_with_llm() above.
# Use extract(text, use_llm=True) to enable it.

# Confidence scores are returned per field alongside extracted values.
# A confidence of 0.8 means regex matched; 0.0 means field not found.
