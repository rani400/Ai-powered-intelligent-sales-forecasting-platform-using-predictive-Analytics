"""CSV parsing helpers; intentionally no IO or database access."""
from app.schemas.lead import LeadCreate


CSV_FIELDS = set(LeadCreate.model_fields)


def normalize_csv_row(row: dict) -> dict:
    data = {}
    for key, value in row.items():
        if key is None:
            continue
        key = key.strip().lower().replace(' ', '_')
        if key not in CSV_FIELDS:
            continue
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                value = None
        if key == 'lead_status' and isinstance(value, str):
            value = value.title()
        if key == 'is_active' and isinstance(value, str):
            if value.lower() in {'true', 'yes', '1'}:
                value = True
            elif value.lower() in {'false', 'no', '0'}:
                value = False
        data[key] = value
    return data
