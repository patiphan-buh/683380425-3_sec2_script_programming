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
