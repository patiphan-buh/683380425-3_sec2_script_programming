# agentic-data-processor/src/conversion_tasks.py
import json
import csv
from .utils import setup_logging

logger = setup_logging(__name__)

class ConversionTasks:
    """
    Handles conversions between CSV (list of dicts) and JSON formats.
    """
    def __init__(self):
        logger.info("ConversionTasks initialized.")

    def csv_to_json(self, csv_data):
        """
        Converts CSV data (list of dictionaries) to JSON-compatible Python list of dicts.
        Numeric strings are converted to actual numbers.
        """
        if not csv_data:
            logger.warning("No CSV data to convert to JSON.")
            return []

        json_data = []
        for row in csv_data:
            json_row = {}
            for key, value in row.items():
                try:
                    # Attempt to convert to int or float
                    if value.strip().isdigit():
                        json_row[key] = int(value)
                    elif value.strip().replace('.', '', 1).isdigit():
                        json_row[key] = float(value)
                    elif value.strip().lower() in ['true', 'false']:
                        json_row[key] = value.strip().lower() == 'true'
                    elif value.strip().lower() == 'null' or value.strip() == '':
                        json_row[key] = None
                    else:
                        json_row[key] = value.strip()
                except Exception as e:
                    logger.debug(f"Could not convert value '{value}' for key '{key}' to numeric/boolean type. Keeping as string. Error: {e}")
                    json_row[key] = value.strip()
            json_data.append(json_row)

        logger.info(f"Converted {len(csv_data)} CSV rows to JSON format.")
        return json_data

    def json_to_csv(self, json_data, fieldnames=None):
        """
        Converts JSON data (list of dictionaries) to a CSV-compatible list of dictionaries.
        Assumes flat JSON objects or flattens simple nested keys (e.g. details.brand).
        """
        if not json_data:
            logger.warning("No JSON data to convert to CSV.")
            return [], []

        csv_rows = []

        # If fieldnames not provided, attempt to collect all unique keys, including from nested 'details'
        if fieldnames is None:
            all_keys = set()
            for item in json_data:
                for k, v in item.items():
                    if isinstance(v, dict):  # For simple nested dicts like 'details'
                        for sub_k in v.keys():
                            all_keys.add(f"{k}.{sub_k}")  # e.g., 'details.brand'
                    elif isinstance(v, list):  # For lists, just add the key, won't flatten items
                        all_keys.add(k)
                    else:
                        all_keys.add(k)
            fieldnames = sorted(list(all_keys))
            logger.info(f"Inferred fieldnames for JSON to CSV: {fieldnames}")

        for item in json_data:
            row = {}
            for field in fieldnames:
                if '.' in field:  # Handle simple nested keys
                    parts = field.split('.')
                    current_val = item.get(parts[0])
                    if isinstance(current_val, dict):
                        row[field] = current_val.get(parts[1], '')
                    else:
                        row[field] = ''  # Nested path not found or not a dict
                else:
                    value = item.get(field, '')
                    if isinstance(value, (dict, list)):  # Convert complex types to string representation
                        row[field] = json.dumps(value)
                    else:
                        row[field] = value
            csv_rows.append(row)

        logger.info(f"Converted {len(json_data)} JSON objects to CSV format.")
        return csv_rows, fieldnames
