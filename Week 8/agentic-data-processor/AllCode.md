# agentic-data-processor – All Code

## `agentic-data-processor/main.py`

```python
# agentic-data-processor/main.py
import os
from src.config_parser import ConfigParser
from src.data_agent import DataAgent
from src.utils import setup_logging

logger = setup_logging(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    # ทำให้ path ใน config (เช่น data/input_sales.csv) อิงจากโฟลเดอร์โปรเจกต์เสมอ
    os.chdir(BASE_DIR)

    config_path = os.path.join(BASE_DIR, "configs", "data_pipeline_config.json")
    config = ConfigParser(config_path).load_config()

    agent = DataAgent(config)
    agent.run()

if __name__ == "__main__":
    main()

```

## `agentic-data-processor/src/__init__.py`

```python
# agentic-data-processor/src/__init__.py
# This file indicates that the 'src' directory is a Python package.

```

## `agentic-data-processor/src/utils.py`

```python
# agentic-data-processor/src/utils.py
import logging
import os
import json
import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_logging(name, level=logging.INFO, log_file=None):
    """Sets up a logger for specific modules, allowing file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Ensure handlers are added only once per logger instance
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler (optional)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

def ensure_directory_exists(path):
    """Ensures that a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        logging.info(f"Directory ensured: {path}")
    except OSError as e:
        logging.error(f"Error creating directory {path}: {e}")
        raise

def log_audit_entry(audit_log_list, status, message, task_type="N/A", details=None):
    """Adds an entry to the audit log list."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "status": status,
        "task_type": task_type,
        "message": message,
        "details": details if details else {}
    }
    audit_log_list.append(log_entry)
    if status == "ERROR" or status == "CRITICAL":
        logging.error(f"AUDIT LOG - {status}: {message} | Task: {task_type} | Details: {details}")
    else:
        logging.info(f"AUDIT LOG - {status}: {message} | Task: {task_type}")

```

## `agentic-data-processor/src/config_parser.py`

```python
# agentic-data-processor/src/config_parser.py
import json
import os
from .utils import setup_logging

logger = setup_logging(__name__)

class ConfigParser:
    """
    Parses and validates the data automation configuration from a JSON file.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}

    def load_config(self):
        """Loads the configuration from the specified JSON file."""
        if not os.path.exists(self.config_path):
            logger.critical(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self._validate_config()
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self.config
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format in config file: {e}")
            raise ValueError(f"Invalid JSON format in config file: {e}")
        except Exception as e:
            logger.critical(f"An error occurred while loading config: {e}")
            raise Exception(f"An error occurred while loading config: {e}")

    def _validate_config(self):
        """
        Validates the loaded configuration to ensure required fields and task structures are present.
        This validation can be extended based on all possible task types.
        """
        required_top_level_fields = ["tasks"]
        for field in required_top_level_fields:
            if field not in self.config:
                raise ValueError(f"Missing required field in config: '{field}'")

        if not isinstance(self.config["tasks"], list):
            raise ValueError("Config field 'tasks' must be a list.")

        # Basic validation for each task
        for i, task in enumerate(self.config["tasks"]):
            if "type" not in task:
                raise ValueError(f"Task {i} is missing 'type' field.")
            # ยกเว้นการเช็ค output_data_key สำหรับงานประเภท save_csv และ save_json
            if task["type"] not in ["save_csv", "save_json"] and "output_data_key" not in task:
                raise ValueError(f"Task {i} (type: {task['type']}) is missing 'output_data_key' field.")

            # Specific validations per task type
            if task["type"] in ["load_csv", "load_json", "save_csv", "save_json"]:
                if "file_path" not in task:
                    raise ValueError(f"Task {i} (type: {task['type']}) requires 'file_path'.")

            if task["type"] == "save_csv":
                if "fieldnames" not in task and "input_data_key" not in task:
                    # For saving, either fieldnames must be explicit or derived from input_data
                    logger.warning(f"Task {i} (save_csv) has no explicit 'fieldnames'. Will attempt to derive from data.")

            if task["type"] in ["transform_csv_aggregate", "filter_csv"]:
                if "input_data_key" not in task:
                    raise ValueError(f"Task {i} (type: {task['type']}) requires 'input_data_key'.")

            if task["type"] == "csv_to_json_conversion" or task["type"] == "json_to_csv_conversion":
                if "input_data_key" not in task:
                    raise ValueError(f"Task {i} (type: {task['type']}) requires 'input_data_key'.")

            # Add more specific validations as needed for task parameters

        logger.info("Configuration validated.")

```

## `agentic-data-processor/src/csv_tasks.py`

```python
# agentic-data-processor/src/csv_tasks.py
import csv
import os
from collections import defaultdict
from .utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class CSVTasks:
    """
    Handles advanced reading, writing, and processing of CSV files.
    All data is handled as a list of dictionaries.
    """
    def __init__(self):
        logger.info("CSVTasks initialized.")

    def load_csv(self, file_path):
        """
        Loads a CSV file and returns its content as a list of dictionaries.
        Assumes the first row is the header.
        """
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found: {file_path}")
            return None

        data = []
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
            logger.info(f"Successfully loaded {len(data)} rows from '{file_path}'.")
            return data
        except Exception as e:
            logger.error(f"Error loading CSV file '{file_path}': {e}")
            return None

    def save_csv(self, data, file_path, fieldnames=None):
        """
        Saves a list of dictionaries to a CSV file.
        `fieldnames` can be explicitly provided or inferred from the first dictionary.
        """
        if not data:
            logger.warning("No data provided to save to CSV. File will be empty or not created.")
            return False

        ensure_directory_exists(os.path.dirname(file_path))

        if fieldnames is None:
            # Infer fieldnames from the first dictionary
            if isinstance(data[0], dict):
                fieldnames = list(data[0].keys())
                logger.info(f"Inferred fieldnames for CSV: {fieldnames}")
            else:
                logger.error("Cannot infer fieldnames: data is not a list of dictionaries.")
                return False

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"Successfully saved {len(data)} rows to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving CSV file '{file_path}': {e}")
            return False

    def transform_csv_aggregate(self, data, group_by_field, aggregate_field, aggregate_type="sum"):
        """
        Aggregates CSV data (list of dicts) by a specified field.
        Supports 'sum', 'count', 'average'.
        Assumes aggregate_field can be converted to float for sum/average.
        """
        if not data:
            logger.warning("No data to aggregate.")
            return []

        aggregated_data = defaultdict(lambda: {'_count': 0, '_sum': 0.0})

        for row in data:
            group_value = row.get(group_by_field)
            if group_value is None:
                logger.warning(f"Skipping row due to missing group_by_field '{group_by_field}': {row}")
                continue

            try:
                numeric_value = float(row.get(aggregate_field, 0))  # Default to 0 if field missing
                aggregated_data[group_value]['_sum'] += numeric_value
                aggregated_data[group_value]['_count'] += 1
            except ValueError as e:
                logger.warning(f"Skipping aggregation for row due to non-numeric '{aggregate_field}': {row}. Error: {e}")
                continue
            except TypeError as e:
                logger.warning(f"Skipping aggregation for row due to missing aggregate_field '{aggregate_field}': {row}. Error: {e}")
                continue

        results = []
        for group_value, metrics in aggregated_data.items():
            result_row = {group_by_field: group_value}
            if aggregate_type == "sum":
                result_row[f'Total_{aggregate_field}'] = round(metrics['_sum'], 2)
            elif aggregate_type == "count":
                result_row[f'Count_{aggregate_field}'] = metrics['_count']
            elif aggregate_type == "average":
                result_row[f'Average_{aggregate_field}'] = round(metrics['_sum'] / metrics['_count'], 2) if metrics['_count'] > 0 else 0.0
            else:
                logger.warning(f"Unsupported aggregation type: {aggregate_type}. Skipping for group {group_value}.")
                continue
            results.append(result_row)

        logger.info(f"Aggregated data by '{group_by_field}' using '{aggregate_type}'. Produced {len(results)} rows.")
        return results

    def filter_csv(self, data, filter_field, operator, value):
        """
        Filters CSV data (list of dicts) based on a condition.
        `operator` can be '>', '<', '>=', '<=', '==', '!='.
        `value` will be converted to appropriate type if possible.
        """
        if not data:
            logger.warning("No data to filter.")
            return []

        filtered_data = []
        for row in data:
            field_value = row.get(filter_field)
            if field_value is None:
                logger.debug(f"Skipping row in filter due to missing field '{filter_field}': {row}")
                continue

            try:
                # Attempt type conversion for comparison
                if isinstance(value, (int, float)):
                    compare_value = float(field_value)
                else:  # Default to string comparison
                    compare_value = str(field_value)

                condition_met = False
                if operator == '>':
                    condition_met = compare_value > value
                elif operator == '<':
                    condition_met = compare_value < value
                elif operator == '>=':
                    condition_met = compare_value >= value
                elif operator == '<=':
                    condition_met = compare_value <= value
                elif operator == '==':
                    condition_met = compare_value == value
                elif operator == '!=':
                    condition_met = compare_value != value
                else:
                    logger.warning(f"Unsupported filter operator: '{operator}'. Skipping filter for row.")
                    continue

                if condition_met:
                    filtered_data.append(row)
            except ValueError as e:
                logger.warning(f"Type conversion error during filter for row: {row}. Error: {e}")
            except Exception as e:
                logger.warning(f"General error during filter for row: {row}. Error: {e}")

        logger.info(f"Filtered data by '{filter_field} {operator} {value}'. Resulted in {len(filtered_data)} rows.")
        return filtered_data

```

## `agentic-data-processor/src/json_tasks.py`

```python
# agentic-data-processor/src/json_tasks.py
import json
import os
from .utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class JSONTasks:
    """
    Handles advanced reading, writing, and manipulation of JSON data.
    """
    def __init__(self):
        logger.info("JSONTasks initialized.")

    def load_json(self, file_path):
        """Loads a JSON file and returns the Python object."""
        if not os.path.exists(file_path):
            logger.error(f"JSON file not found: {file_path}")
            return None

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"Successfully loaded JSON from '{file_path}'.")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading JSON file '{file_path}': {e}")
            return None

    def save_json(self, data, file_path, indent=2):
        """Saves a Python object to a JSON file, with pretty-printing."""
        ensure_directory_exists(os.path.dirname(file_path))
        try:
            with open(file_path, mode='w', encoding='utf-8') as file:
                json.dump(data, file, indent=indent, ensure_ascii=False)
            logger.info(f"Successfully saved JSON to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON file '{file_path}': {e}")
            return False

    def update_json_data(self, data, updates):
        """
        Applies updates to a JSON-like Python object.
        `updates` is a list of dicts: [{"path": "key1.key2", "value": "new_value"}, ...]
        Handles nested paths.
        """
        if not data:
            logger.warning("No JSON data provided for update.")
            return data

        modified_data = json.loads(json.dumps(data))  # Deep copy to avoid modifying original reference

        for update in updates:
            path = update.get("path")
            value = update.get("value")
            operation = update.get("operation", "set")  # 'set', 'add_to_list', 'remove_from_list'

            if path is None:
                logger.warning(f"Update skipped: missing 'path' in update: {update}")
                continue

            keys = path.split('.')
            current_node = modified_data

            try:
                # Navigate to the parent of the target key
                for i in range(len(keys) - 1):
                    key = keys[i]
                    if isinstance(current_node, dict):
                        if key not in current_node:
                            logger.warning(f"Path '{path}' not found at key '{key}'. Skipping update: {update}")
                            current_node = None  # Mark as not found
                            break
                        current_node = current_node[key]
                    elif isinstance(current_node, list) and key.isdigit():
                        index = int(key)
                        if 0 <= index < len(current_node):
                            current_node = current_node[index]
                        else:
                            logger.warning(f"Path '{path}' not found: index '{key}' out of bounds for list. Skipping update: {update}")
                            current_node = None
                            break
                    else:
                        logger.warning(f"Path '{path}' not navigable at key '{key}' (expected dict/list, got {type(current_node)}). Skipping update: {update}")
                        current_node = None
                        break

                if current_node is None:  # Path not found during navigation
                    continue

                target_key = keys[-1]

                if operation == "set":
                    if isinstance(current_node, dict):
                        current_node[target_key] = value
                        logger.info(f"Set '{path}' to '{value}'.")
                    elif isinstance(current_node, list) and target_key.isdigit():
                        index = int(target_key)
                        if 0 <= index < len(current_node):
                            current_node[index] = value
                            logger.info(f"Set '{path}' (list index) to '{value}'.")
                        else:
                            logger.warning(f"List index '{index}' out of bounds for path '{path}'. Skipping set: {update}")
                    else:
                        logger.warning(f"Cannot 'set' value for path '{path}': target is not dict or list index. Skipping update: {update}")

                elif operation == "add_to_list":
                    # รองรับกรณี Root Data เป็น List (path เป็น "")
                    if isinstance(current_node, list) and (path == "" or target_key == ""):
                        current_node.append(value)
                        logger.info(f"Added '{value}' to root list.")
                    # กรณี List ซ้อนอยู่ใน Dict
                    elif isinstance(current_node, dict) and target_key in current_node and isinstance(current_node[target_key], list):
                        current_node[target_key].append(value)
                        logger.info(f"Added '{value}' to list at '{path}'.")
                    else:
                        logger.warning(f"Cannot 'add_to_list' for path '{path}': target is not a list. Skipping update: {update}")

                elif operation == "remove_from_list":
                    if isinstance(current_node, dict) and target_key in current_node and isinstance(current_node[target_key], list):
                        if value in current_node[target_key]:
                            current_node[target_key].remove(value)
                            logger.info(f"Removed '{value}' from list at '{path}'.")
                        else:
                            logger.warning(f"Value '{value}' not found in list at '{path}'. Skipping remove: {update}")
                    else:
                        logger.warning(f"Cannot 'remove_from_list' for path '{path}': target is not a list. Skipping update: {update}")
                else:
                    logger.warning(f"Unsupported operation '{operation}' for path '{path}'. Skipping update: {update}")
            except Exception as e:
                logger.error(f"Error applying JSON update for path '{path}': {e}. Update: {update}")

        return modified_data

    def query_json_data(self, data, path):
        """
        Queries a specific element from nested JSON data using a dot-notation path.
        Returns the value or None if not found.
        """
        if not data:
            logger.warning("No JSON data to query.")
            return None

        keys = path.split('.')
        current_node = data

        try:
            for key in keys:
                if isinstance(current_node, dict):
                    current_node = current_node.get(key)
                elif isinstance(current_node, list) and key.isdigit():
                    index = int(key)
                    if 0 <= index < len(current_node):
                        current_node = current_node[index]
                    else:
                        logger.warning(f"Query path '{path}' failed: index '{key}' out of bounds for list.")
                        return None
                else:
                    logger.warning(f"Query path '{path}' failed: cannot navigate through {type(current_node)} with key '{key}'.")
                    return None

                if current_node is None:
                    logger.debug(f"Query path '{path}' led to None at key '{key}'.")
                    return None

            logger.info(f"Successfully queried '{path}'. Result: {current_node}")
            return current_node
        except Exception as e:
            logger.error(f"Error querying JSON data with path '{path}': {e}")
            return None

```

## `agentic-data-processor/src/conversion_tasks.py`

```python
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

```

## `agentic-data-processor/src/data_agent.py`

```python
# agentic-data-processor/src/data_agent.py
import os
import json
import datetime
import sys
from .utils import setup_logging, log_audit_entry, ensure_directory_exists
from .csv_tasks import CSVTasks
from .json_tasks import JSONTasks
from .conversion_tasks import ConversionTasks

logger = setup_logging(__name__)

class DataAgent:
    """
    An agent that processes various data formats (CSV, JSON) based on a
    structured configuration file, managing internal data state.
    """
    def __init__(self, config):
        self.config = config
        self.audit_log = []
        self.data_store = {}  # Stores intermediate data results {key: data_object}
        self.start_time = datetime.datetime.now()

        self.csv_tasks = CSVTasks()
        self.json_tasks = JSONTasks()
        self.conversion_tasks = ConversionTasks()
        logger.info("Data Agent initialized with configuration.")

    def _get_data_from_store(self, key):
        """Retrieves data from the data store."""
        if key not in self.data_store:
            logger.error(f"Data key '{key}' not found in agent's data store.")
            return None
        return self.data_store[key]

    def _set_data_in_store(self, key, data):
        """Stores data in the data store."""
        self.data_store[key] = data
        logger.debug(f"Data stored under key: '{key}'.")

    def _process_task(self, task):
        """Dispatches a task to the appropriate handler and manages data state."""
        task_type = task.get("type")
        task_name = task.get("name", task_type)
        input_data_key = task.get("input_data_key")    # Key to retrieve input data from store
        output_data_key = task.get("output_data_key")  # Key to store output data in store

        logger.info(f"Executing task: '{task_name}' (Type: {task_type})")
        log_audit_entry(self.audit_log, "INFO", f"Starting task '{task_name}'", task_type, task)

        current_data = None
        if input_data_key:
            current_data = self._get_data_from_store(input_data_key)
            if current_data is None and task_type not in ["load_csv", "load_json"]:
                # For tasks that require existing data, log an error if input_data_key is missing
                log_audit_entry(self.audit_log, "ERROR", f"Task '{task_name}' failed: Required input data '{input_data_key}' not found in store.", task_type, task)
                logger.error(f"Task '{task_name}' failed: Input data '{input_data_key}' not found.")
                return

        try:
            success = False
            task_output_data = None  # Data produced by the task to be stored

            if task_type == "load_csv":
                file_path = task.get("file_path")
                task_output_data = self.csv_tasks.load_csv(file_path)
                success = task_output_data is not None
            elif task_type == "save_csv":
                file_path = task.get("file_path")
                fieldnames = task.get("fieldnames")
                success = self.csv_tasks.save_csv(current_data, file_path, fieldnames)
            elif task_type == "transform_csv_aggregate":
                group_by_field = task.get("group_by_field")
                aggregate_field = task.get("aggregate_field")
                aggregate_type = task.get("aggregate_type", "sum")
                task_output_data = self.csv_tasks.transform_csv_aggregate(current_data, group_by_field, aggregate_field, aggregate_type)
                success = task_output_data is not None
            elif task_type == "filter_csv":
                filter_field = task.get("filter_field")
                operator = task.get("operator")
                value = task.get("value")
                task_output_data = self.csv_tasks.filter_csv(current_data, filter_field, operator, value)
                success = task_output_data is not None

            elif task_type == "load_json":
                file_path = task.get("file_path")
                task_output_data = self.json_tasks.load_json(file_path)
                success = task_output_data is not None
            elif task_type == "save_json":
                file_path = task.get("file_path")
                indent = task.get("indent", 2)
                success = self.json_tasks.save_json(current_data, file_path, indent)
            elif task_type == "update_json_data":
                updates = task.get("updates")  # List of update operations
                task_output_data = self.json_tasks.update_json_data(current_data, updates)
                success = task_output_data is not None
            elif task_type == "query_json_data":
                path = task.get("path")
                query_result = self.json_tasks.query_json_data(current_data, path)
                # For query, the result is often just logged or used in subsequent logic
                log_audit_entry(self.audit_log, "INFO", f"Query result for path '{path}': {query_result}", task_type, {"query_path": path, "result": query_result})
                success = True  # Query itself is usually successful if it runs, even if result is None
                task_output_data = query_result  # Store query result for potential chaining

            elif task_type == "csv_to_json_conversion":
                task_output_data = self.conversion_tasks.csv_to_json(current_data)
                success = task_output_data is not None
            elif task_type == "json_to_csv_conversion":
                fieldnames = task.get("fieldnames")
                csv_data, inferred_fieldnames = self.conversion_tasks.json_to_csv(current_data, fieldnames)
                task_output_data = csv_data
                # If fieldnames were inferred, they should be passed to the save_csv task later.
                # For now, just store the data. The next 'save_csv' task would need to use
                # `inferred_fieldnames` or have its own `fieldnames` config. This is a current limitation.
                success = task_output_data is not None
            else:
                log_audit_entry(self.audit_log, "WARNING", f"Unsupported task type: {task_type}", task_type, task)
                logger.warning(f"Unsupported task type: {task_type}")
                return  # Do not log as success/failure for unknown task

            # Store the output data if the task was successful and produced data
            if success and task_output_data is not None and output_data_key:
                self._set_data_in_store(output_data_key, task_output_data)

            if success:
                log_audit_entry(self.audit_log, "SUCCESS", f"Task '{task_name}' completed successfully.", task_type, task)
            else:
                log_audit_entry(self.audit_log, "ERROR", f"Task '{task_name}' failed.", task_type, task)

        except Exception as e:
            log_audit_entry(self.audit_log, "ERROR", f"An error occurred during task '{task_name}': {e}", task_type, {"error": str(e), "task_details": task})
            logger.error(f"Error during task '{task_name}': {e}", exc_info=True)

    def _generate_audit_report(self, output_dir="reports"):
        """Generates a JSON audit report."""
        ensure_directory_exists(output_dir)
        report_filename = f"audit_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(output_dir, report_filename)

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.audit_log, f, indent=4, ensure_ascii=False)
            logger.info(f"Audit report saved to: {report_path}")
            log_audit_entry(self.audit_log, "INFO", f"Audit report generated at {report_path}", "audit_report")
        except Exception as e:
            logger.error(f"Failed to save audit report: {e}")
            log_audit_entry(self.audit_log, "CRITICAL", f"Failed to save audit report: {e}", "audit_report")

    def run(self):
        """Executes all tasks defined in the configuration."""
        logger.info("Starting Data Agent run...")
        log_audit_entry(self.audit_log, "INFO", "Data Agent started.", "agent_run")

        for task in self.config.get("tasks", []):
            self._process_task(task)

        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        log_audit_entry(self.audit_log, "INFO", f"Data Agent finished in {duration:.2f} seconds.", "agent_run_summary")
        logger.info(f"Data Agent finished. Total time: {duration:.2f} seconds.")

        # Save audit report in a dedicated 'reports' subfolder within the base directory
        base_dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
        self._generate_audit_report(os.path.join(base_dir, 'reports'))

```

## `agentic-data-processor/configs/data_pipeline_config.json`

```json
{
  "tasks": [
    {
      "name": "Load raw sales CSV",
      "type": "load_csv",
      "file_path": "data/input_sales.csv",
      "output_data_key": "raw_sales"
    },
    {
      "name": "Filter big sales (Amount >= 100)",
      "type": "filter_csv",
      "input_data_key": "raw_sales",
      "filter_field": "Amount",
      "operator": ">=",
      "value": 100.0,
      "output_data_key": "big_sales"
    },
    {
      "name": "Aggregate total sales by customer",
      "type": "transform_csv_aggregate",
      "input_data_key": "raw_sales",
      "group_by_field": "Customer",
      "aggregate_field": "Amount",
      "aggregate_type": "sum",
      "output_data_key": "sales_by_customer"
    },
    {
      "name": "Save processed sales by customer",
      "type": "save_csv",
      "input_data_key": "sales_by_customer",
      "file_path": "data/processed_sales_by_customer.csv"
    },
    {
      "name": "Convert sales CSV to JSON",
      "type": "csv_to_json_conversion",
      "input_data_key": "raw_sales",
      "output_data_key": "sales_json"
    },
    {
      "name": "Save sales data as JSON",
      "type": "save_json",
      "input_data_key": "sales_json",
      "file_path": "data/sales_data.json",
      "indent": 2
    },
    {
      "name": "Load inventory JSON",
      "type": "load_json",
      "file_path": "data/input_inventory.json",
      "output_data_key": "inventory"
    },
    {
      "name": "Query first product name",
      "type": "query_json_data",
      "input_data_key": "inventory",
      "path": "0.name",
      "output_data_key": "first_product_name"
    },
    {
      "name": "Update stock and add new product",
      "type": "update_json_data",
      "input_data_key": "inventory",
      "updates": [
        {"path": "0.stock", "value": 60, "operation": "set"},
        {"path": "2.stock", "value": 75, "operation": "set"},
        {
          "path": "",
          "operation": "add_to_list",
          "value": {
            "id": "PROD004",
            "name": "Gaming Headset",
            "category": "Audio",
            "stock": 90,
            "details": {"brand": "SoundBlaster", "features": ["Noise Cancelling", "RGB"]}
          }
        }
      ],
      "output_data_key": "updated_inventory"
    },
    {
      "name": "Save updated inventory",
      "type": "save_json",
      "input_data_key": "updated_inventory",
      "file_path": "data/updated_inventory.json",
      "indent": 2
    }
  ]
}

```

## `agentic-data-processor/data/input_sales.csv`

```csv
OrderID,Product,Amount,Price,Customer
101,Laptop,1200.50,1200.50,Alice
102,Mouse,25.00,25.00,Bob
103,Keyboard,75.25,75.25,Alice
104,Monitor,300.00,300.00,Charlie
105,Webcam,45.75,45.75,Bob
106,External HDD,90.00,90.00,David
107,Headphones,150.00,150.00,Alice
108,USB Hub,15.50,15.50,Eve

```

## `agentic-data-processor/data/input_inventory.json`

```json
[
  {
    "id": "PROD001",
    "name": "Laptop Pro",
    "category": "Electronics",
    "stock": 50,
    "details": {
      "brand": "TechCorp",
      "model": "XPS 15"
    }
  },
  {
    "id": "PROD002",
    "name": "Mechanical Keyboard",
    "category": "Peripherals",
    "stock": 120,
    "details": {
      "brand": "KeyMaster",
      "layout": "US ANSI"
    }
  },
  {
    "id": "PROD003",
    "name": "Ergonomic Mouse",
    "category": "Peripherals",
    "stock": 80,
    "details": {
      "brand": "ErgoGear",
      "dpi": 1600
    }
  }
]

```

## `agentic-data-processor/.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
env/
.venv/
.vscode/
.env

# Generated data/output และ reports ถูก commit เพื่อเป็นหลักฐานของ lab

```
