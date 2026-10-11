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
