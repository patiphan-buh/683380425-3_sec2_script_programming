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
