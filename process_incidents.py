#!/usr/bin/env python3
"""
process_incidents.py
Reads raw_incidents.json (ServiceNow fetch output) and writes processed CSV with:
- number, short_description, priority, state, assignment_group, assigned_to,
  sys_created_on, sys_updated_on, sys_id
- age_days (int)
- total_hours (float, 2dp)
- total_days (float, 2dp)
- total_minutes (int)
- sla_breach (bool)  -> total_hours > SLA_HOURS

Config via environment (.env):
INPUT_JSON      default ./raw_incidents.json
OUTPUT_CSV      default ./processed_incidents.csv
SLA_HOURS       default 48
"""
import os
import json
import csv
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

INPUT_JSON = os.getenv("INPUT_JSON", "./raw_incidents.json")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "./processed_incidents.csv")
SLA_HOURS = float(os.getenv("SLA_HOURS", "48"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("process_incidents")


def get_display(rec, field):
    """
    Return human-readable display_value if present, otherwise the raw value,
    otherwise empty string.
    """
    v = rec.get(field)
    if isinstance(v, dict):
        return v.get("display_value") or v.get("value") or ""
    return v or ""


def parse_dt(s):
    """
    Parse ServiceNow datetime strings. Returns naive datetime (UTC assumed if no tz).
    Accepts formats like:
    - "2025-11-14 08:04:55"
    - "2025-11-14 08:04:55.0"
    - "2025-11-14 08:04:55+0000"
    """
    if not s:
        return None
    s = str(s).strip()
    # remove milliseconds if present
    if "." in s and "+" not in s and "-" not in s[11:]:
        # try strip fraction part: "YYYY-MM-DD HH:MM:SS.xxx"
        try:
            s = s.split(".")[0]
        except Exception:
            pass
    formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d")
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt
        except Exception:
            continue
    # As a last resort, try ISO parse
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def main():
    if not os.path.exists(INPUT_JSON):
        raise SystemExit(f"Input JSON not found: {INPUT_JSON}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ServiceNow standard: {"result": [ {...}, {...} ]}
    if isinstance(data, dict) and "result" in data:
        records = data["result"]
    elif isinstance(data, list):
        records = data
    else:
        logger.error("Unexpected JSON structure; expected dict with 'result' or list.")
        return

    logger.info("Loaded %d records from %s", len(records), INPUT_JSON)

    fields = [
        "number",
        "short_description",
        "priority",
        "state",
        "assignment_group",
        "assigned_to",
        "sys_created_on",
        "sys_updated_on",
        "sys_id",
        "age_days",
        "total_hours",
        "total_days",
        "total_minutes",
        "sla_breach",
    ]

    # Use UTC now for consistent arithmetic
    now = datetime.utcnow()

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for rec in records:
            number = get_display(rec, "number")
            short_description = get_display(rec, "short_description")
            priority = get_display(rec, "priority")
            state = get_display(rec, "state")
            assignment_group = get_display(rec, "assignment_group")
            assigned_to = get_display(rec, "assigned_to")
            sys_id = get_display(rec, "sys_id")

            created_str = get_display(rec, "sys_created_on")
            updated_str = get_display(rec, "sys_updated_on")

            created_dt = parse_dt(created_str)
            updated_dt = parse_dt(updated_str)

            age_days = ""
            total_hours = ""
            total_days = ""
            total_minutes = ""
            sla_breach = False

            if updated_dt:
                # If parsed dt has no tz, treat as naive UTC (consistent with fetch)
                # Compute difference using UTC now
                delta = now - updated_dt
                # integer days
                age_days = delta.days
                # hours with 2 decimal places
                total_hours = round(delta.total_seconds() / 3600.0, 2)
                total_days = round(delta.total_seconds() / (3600.0 * 24.0), 2)
                total_minutes = int(round(delta.total_seconds() / 60.0))
                sla_breach = total_hours > SLA_HOURS

            row = {
                "number": number,
                "short_description": short_description,
                "priority": priority,
                "state": state,
                "assignment_group": assignment_group,
                "assigned_to": assigned_to,
                "sys_created_on": created_str,
                "sys_updated_on": updated_str,
                "sys_id": sys_id,
                "age_days": age_days,
                "total_hours": total_hours,
                "total_days": total_days,
                "total_minutes": total_minutes,
                "sla_breach": sla_breach,
            }

            writer.writerow(row)

    logger.info("Wrote processed CSV to %s", OUTPUT_CSV)
    logger.info("SLA threshold (hours): %s", SLA_HOURS)


if __name__ == "__main__":
    main()
