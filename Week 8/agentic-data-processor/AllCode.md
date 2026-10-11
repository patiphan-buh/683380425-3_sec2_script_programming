# agentic-data-processor – All Code

## `agentic-data-processor/main.py`

```python
# agentic-data-processor/main.py
import sys
import os
import json

# Add the 'src' directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from agent import DataPipelineAgent
from utils import setup_logging

logger = setup_logging(__name__)

def main():
    config_path = os.path.join(BASE_DIR, 'configs', 'data_pipeline_config.json')
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    agent = DataPipelineAgent(config, BASE_DIR)
    report_path = agent.run()
    logger.info(f"Done. See report: {report_path}")

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

## `agentic-data-processor/src/csv_handler.py`

```python
# agentic-data-processor/src/csv_handler.py
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

## `agentic-data-processor/src/json_handler.py`

```python
# agentic-data-processor/src/json_handler.py
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

## `agentic-data-processor/src/agent.py`

```python
# agentic-data-processor/src/agent.py
"""
A small rule-based "agent": it reads a JSON config, builds a plan (list of steps),
executes each step, observes the result, decides whether to continue, and finally
writes an audit report. No external LLM is needed - the 'agentic' part is the
Plan -> Act -> Observe -> Report loop driven entirely by configuration.
"""
import os
from datetime import datetime
from csv_handler import CSVHandler
from json_handler import JSONHandler
from utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)


class DataPipelineAgent:
    def __init__(self, config, base_dir):
        self.cfg = config
        self.base_dir = base_dir
        self.csv = CSVHandler()
        self.json = JSONHandler()
        self.state = {}          # shared memory between steps
        self.audit = []          # list of (step, status, detail)

    # ---------- helpers ----------
    def _path(self, rel):
        return os.path.join(self.base_dir, rel)

    def _log(self, step, status, detail):
        self.audit.append((step, status, detail))
        getattr(logger, "info" if status in ("OK", "INFO") else "warning")(f"[{step}] {status}: {detail}")

    # ---------- PLAN ----------
    def plan(self):
        steps = ["load_csv", "validate_csv", "process_csv", "write_csv",
                 "load_json", "validate_json", "update_json", "write_json"]
        self._log("plan", "INFO", f"Planned {len(steps)} steps: {', '.join(steps)}")
        return steps

    # ---------- ACT ----------
    def load_csv(self):
        data = self.csv.read_csv_as_dicts(self._path(self.cfg["inputs"]["sales_csv"]))
        if not data:
            return False, "could not read sales CSV"
        self.state["sales"] = data
        return True, f"loaded {len(data)} rows"

    def validate_csv(self):
        required = self.cfg["csv_rules"]["required_columns"]
        cols = list(self.state["sales"][0].keys())
        missing = [c for c in required if c not in cols]
        if missing:
            return False, f"missing columns: {missing}"
        bad = 0
        for row in self.state["sales"]:
            try:
                float(row["Amount"]); float(row["Price"])
            except (ValueError, TypeError):
                bad += 1
        return True, f"columns OK; {bad} row(s) with non-numeric Amount/Price"

    def process_csv(self):
        res = self.csv.process_sales_data(
            self.state["sales"], min_sale_amount=self.cfg["csv_rules"]["min_sale_amount"])
        self.state["csv_result"] = res
        s = res["summary"]
        return True, (f"total={s['Total Sales']}, avg_price={s['Average Item Price']}, "
                      f"filtered={s['Filtered Sales Count']}")

    def write_csv(self):
        res = self.state["csv_result"]
        s = res["summary"]
        fields = list(self.state["sales"][0].keys())
        summary_row = {'OrderID': 'SUMMARY', 'Product': 'Total/Avg', 'Amount': s['Total Sales'],
                       'Price': s['Average Item Price'], 'Customer': f"Count: {s['Filtered Sales Count']}"}
        out = self._path(self.cfg["outputs"]["filtered_sales_csv"])
        ok = self.csv.write_dicts_to_csv(res["filtered_sales"] + [summary_row], out, fields)
        return ok, f"wrote {os.path.relpath(out, self.base_dir)}"

    def load_json(self):
        data = self.json.read_json(self._path(self.cfg["inputs"]["inventory_json"]))
        if data is None:
            return False, "could not read inventory JSON"
        self.state["inventory"] = data
        return True, f"loaded {len(data)} products"

    def validate_json(self):
        required = self.cfg["json_rules"]["required_keys"]
        problems = [p.get("id", "?") for p in self.state["inventory"]
                    if any(k not in p for k in required)]
        if problems:
            return False, f"products missing required keys: {problems}"
        return True, "all products have required keys"

    def update_json(self):
        inv = self.state["inventory"]
        notes = []
        for u in self.cfg["json_rules"]["stock_updates"]:
            ok = self.json.update_inventory(inv, u["id"], u["new_stock"])
            notes.append(f"{u['id']}->{u['new_stock']}:{'updated' if ok else 'NOT FOUND'}")
        existing = {p["id"] for p in inv}
        for p in self.cfg["json_rules"]["new_products"]:
            if p["id"] in existing:
                notes.append(f"{p['id']}:skipped(duplicate)")
            else:
                self.json.add_product(inv, p)
                notes.append(f"{p['id']}:added")
        return True, "; ".join(notes)

    def write_json(self):
        out = self._path(self.cfg["outputs"]["updated_inventory_json"])
        ok = self.json.write_json(self.state["inventory"], out, indent=2)
        return ok, f"wrote {os.path.relpath(out, self.base_dir)}"

    # ---------- LOOP + REPORT ----------
    def run(self):
        started = datetime.now()
        for step in self.plan():
            ok, detail = getattr(self, step)()          # Act
            self._log(step, "OK" if ok else "FAIL", detail)   # Observe
            if not ok:                                   # Decide
                self._log("agent", "FAIL", f"Stopping pipeline at '{step}'")
                break
        return self.write_report(started)

    def write_report(self, started):
        report_dir = self._path(self.cfg["outputs"]["report_dir"])
        ensure_directory_exists(report_dir)
        stamp = started.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(report_dir, f"audit_report_{stamp}.txt")
        fails = sum(1 for _, s, _ in self.audit if s == "FAIL")
        warns = sum(1 for _, s, _ in self.audit if "NOT FOUND" in _ or "skipped" in _)
        lines = [f"AUDIT REPORT - {self.cfg['pipeline_name']}",
                 f"Started : {started:%Y-%m-%d %H:%M:%S}",
                 f"Finished: {datetime.now():%Y-%m-%d %H:%M:%S}",
                 f"Result  : {'SUCCESS' if fails == 0 else 'FAILED'}",
                 f"Warnings: {warns}", "-" * 60]
        for step, status, detail in self.audit:
            lines.append(f"[{status:<4}] {step:<14} {detail}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        logger.info(f"Audit report written to {path}")
        return path

```

## `agentic-data-processor/configs/data_pipeline_config.json`

```json
{
  "pipeline_name": "week8-agentic-data-pipeline",
  "inputs": {
    "sales_csv": "data/input_sales.csv",
    "inventory_json": "data/input_inventory.json"
  },
  "outputs": {
    "filtered_sales_csv": "data/output_filtered_sales.csv",
    "updated_inventory_json": "data/output_updated_inventory.json",
    "report_dir": "reports"
  },
  "csv_rules": {
    "required_columns": ["OrderID", "Product", "Amount", "Price", "Customer"],
    "min_sale_amount": 100.0
  },
  "json_rules": {
    "required_keys": ["id", "name", "category", "stock", "details"],
    "stock_updates": [
      {"id": "PROD001", "new_stock": 60},
      {"id": "PROD003", "new_stock": 75},
      {"id": "PROD999", "new_stock": 10}
    ],
    "new_products": [
      {
        "id": "PROD004",
        "name": "Gaming Headset",
        "category": "Audio",
        "stock": 90,
        "details": {"brand": "SoundBlaster", "features": ["Noise Cancelling", "RGB"]}
      }
    ]
  }
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

# Generated Data Files
data/output_filtered_sales.csv
data/output_updated_inventory.json

```
