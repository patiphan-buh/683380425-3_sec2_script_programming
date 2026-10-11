# data-processor – All Code

## `data-processor/main.py`

```python
# data-processor/main.py
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from csv_handler import CSVHandler
from json_handler import JSONHandler
from utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

def main():
    """
    Main entry point for the CSV and JSON data processor.
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    ensure_directory_exists(data_dir)

    # --- File Paths ---
    input_csv_path = os.path.join(data_dir, 'input_sales.csv')
    output_filtered_csv_path = os.path.join(data_dir, 'output_filtered_sales.csv')
    input_json_path = os.path.join(data_dir, 'input_inventory.json')
    output_updated_json_path = os.path.join(data_dir, 'output_updated_inventory.json')

    # --- Initialize Handlers ---
    csv_proc = CSVHandler()
    json_proc = JSONHandler()

    logger.info("--- Starting CSV Data Processing Workflow ---")

    # 1. Read CSV data
    sales_data = csv_proc.read_csv_as_dicts(input_csv_path)

    if sales_data:
        # 2. Process sales data (e.g., filter sales >= $100 and get summary)
        min_amount_for_filter = 100.0
        processed_results = csv_proc.process_sales_data(sales_data, min_sale_amount=min_amount_for_filter)
        filtered_sales = processed_results["filtered_sales"]
        sales_summary = processed_results["summary"]
        logger.info(f"Summary of all sales: {sales_summary}")

        # 3. Prepare data for writing, including a summary row
        csv_fieldnames = list(sales_data[0].keys())

        # Add a summary row to the filtered data
        summary_row = {
            'OrderID': 'SUMMARY',
            'Product': 'Total/Avg',
            'Amount': sales_summary['Total Sales'],
            'Price': sales_summary['Average Item Price'],
            'Customer': f"Count: {sales_summary['Filtered Sales Count']}"
        }
        filtered_sales_with_summary = filtered_sales + [summary_row]

        # 4. Write filtered sales data to a new CSV
        csv_proc.write_dicts_to_csv(filtered_sales_with_summary, output_filtered_csv_path, csv_fieldnames)
    else:
        logger.error("No sales data to process from CSV.")

    logger.info("--- Starting JSON Data Processing Workflow ---")

    # 1. Read JSON inventory data
    inventory_data = json_proc.read_json(input_json_path)

    if inventory_data:
        # 2. Update existing product stock
        json_proc.update_inventory(inventory_data, "PROD001", 60)  # Update Laptop Pro stock
        json_proc.update_inventory(inventory_data, "PROD003", 75)  # Update Ergonomic Mouse stock

        # 3. Add a new product
        new_product_entry = {
            "id": "PROD004",
            "name": "Gaming Headset",
            "category": "Audio",
            "stock": 90,
            "details": {
                "brand": "SoundBlaster",
                "features": ["Noise Cancelling", "RGB"]
            }
        }
        json_proc.add_product(inventory_data, new_product_entry)

        # 4. Write updated JSON data to a new file
        json_proc.write_json(inventory_data, output_updated_json_path, indent=2)
    else:
        logger.error("No inventory data to process from JSON.")

    logger.info("--- Data Processing Workflows Completed ---")

if __name__ == "__main__":
    main()

```

## `data-processor/src/__init__.py`

```python
# data-processor/src/__init__.py
# This file indicates that the 'src' directory is a Python package.

```

## `data-processor/src/utils.py`

```python
# data-processor/src/utils.py
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_logging(name, level=logging.INFO):
    """Sets up a logger for specific modules."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:  # Prevent adding multiple handlers if called multiple times
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def ensure_directory_exists(path):
    """Ensures that a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        logging.info(f"Directory ensured: {path}")
    except OSError as e:
        logging.error(f"Error creating directory {path}: {e}")
        raise

```

## `data-processor/src/csv_handler.py`

```python
# data-processor/src/csv_handler.py
import csv
import os
from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)

class CSVHandler:
    """
    Handles reading, writing, and basic processing of CSV files.
    """
    def __init__(self):
        logger.info("CSVHandler initialized.")

    def read_csv_as_dicts(self, file_path):
        """
        Reads a CSV file and returns its content as a list of dictionaries.
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
            logger.info(f"Successfully read {len(data)} rows from '{file_path}'.")
            return data
        except Exception as e:
            logger.error(f"Error reading CSV file '{file_path}': {e}")
            return None

    def write_dicts_to_csv(self, data, file_path, fieldnames):
        """
        Writes a list of dictionaries to a CSV file.
        `fieldnames` must be a list of strings corresponding to dictionary keys for headers.
        """
        if not data:
            logger.warning("No data provided to write to CSV.")
            return False

        ensure_directory_exists(os.path.dirname(file_path))
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"Successfully wrote {len(data)} rows to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error writing CSV file '{file_path}': {e}")
            return False

    def process_sales_data(self, sales_data, min_sale_amount=0):
        """
        Processes sales data: calculates total sales, average price,
        and filters sales above a certain amount.
        Assumes 'Amount' and 'Price' fields are present and convertible to float.
        """
        if not sales_data:
            logger.warning("No sales data provided for processing.")
            return {"filtered_sales": [], "summary": {}}

        total_sales = 0.0
        total_price = 0.0
        num_items = 0
        filtered_sales = []

        for row in sales_data:
            try:
                amount = float(row.get('Amount', 0))
                price = float(row.get('Price', 0))  # Assuming 'Price' per item

                total_sales += amount
                num_items += 1  # Count items for average price
                total_price += price

                if amount >= min_sale_amount:
                    filtered_sales.append(row)
            except ValueError as e:
                logger.warning(f"Skipping row due to data conversion error: {row}. Error: {e}")
            except TypeError as e:
                logger.warning(f"Skipping row due to missing keys or invalid data type: {row}. Error: {e}")

        average_price = total_price / num_items if num_items > 0 else 0.0

        summary = {
            "Total Sales": f"{total_sales:.2f}",
            "Average Item Price": f"{average_price:.2f}",
            "Filtered Sales Count": len(filtered_sales)
        }

        logger.info(f"Sales data processed. Total Sales: {summary['Total Sales']}, Filtered Count: {summary['Filtered Sales Count']}")
        return {"filtered_sales": filtered_sales, "summary": summary}

```

## `data-processor/src/json_handler.py`

```python
# data-processor/src/json_handler.py
import json
import os
from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)

class JSONHandler:
    """
    Handles reading, writing, and basic manipulation of JSON files.
    """
    def __init__(self):
        logger.info("JSONHandler initialized.")

    def read_json(self, file_path):
        """Reads a JSON file and returns the Python object."""
        if not os.path.exists(file_path):
            logger.error(f"JSON file not found: {file_path}")
            return None

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"Successfully read JSON from '{file_path}'.")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading JSON file '{file_path}': {e}")
            return None

    def write_json(self, data, file_path, indent=4):
        """Writes a Python object to a JSON file, with pretty-printing."""
        ensure_directory_exists(os.path.dirname(file_path))
        try:
            with open(file_path, mode='w', encoding='utf-8') as file:
                json.dump(data, file, indent=indent, ensure_ascii=False)
            logger.info(f"Successfully wrote JSON to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file '{file_path}': {e}")
            return False

    def update_inventory(self, inventory_data, product_id, new_stock_level):
        """
        Updates the stock level of a product in nested inventory data.
        Assumes inventory_data is a list of product dictionaries.
        """
        updated = False
        if not isinstance(inventory_data, list):
            logger.warning("Inventory data is not a list. Cannot update.")
            return False

        for product in inventory_data:
            if product.get("id") == product_id:
                product["stock"] = new_stock_level
                logger.info(f"Updated stock for product '{product_id}' to {new_stock_level}.")
                updated = True
                break

        if not updated:
            logger.warning(f"Product '{product_id}' not found in inventory for update.")
        return updated

    def add_product(self, inventory_data, new_product):
        """Adds a new product dictionary to the inventory list."""
        if not isinstance(inventory_data, list):
            logger.warning("Inventory data is not a list. Cannot add product.")
            return False

        inventory_data.append(new_product)
        logger.info(f"Added new product: {new_product.get('name', 'N/A')}.")
        return True

```

## `data-processor/data/input_sales.csv`

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

## `data-processor/data/input_inventory.json`

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

## `data-processor/.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python/
env/
venv/
.ipynb_checkpoints/
.vscode/

# Environment
.env

# Pipenv
.venv/

# virtualenv
venv/
env/

# Generated Data Files (output ถูก commit เพื่อเป็นหลักฐานของ lab)
```
