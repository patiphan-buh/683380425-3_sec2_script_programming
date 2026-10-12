import datetime
import os
import pdf_tasks
import word_tasks
from utils import setup_logging, ensure_dir

logger = setup_logging(__name__)


class DocumentAgent:
    """Runs the tasks listed in the config and writes an audit report."""

    def __init__(self, config, base_dir):
        self.config = config
        self.base = base_dir
        self.audit = []

    def _p(self, rel):
        return os.path.join(self.base, rel)

    def _run(self, task):
        t = task["type"]
        if t == "extract_pdf_text":
            return pdf_tasks.extract_pdf_text(self._p(task["input"]), self._p(task["output"]))
        if t == "merge_pdfs":
            return pdf_tasks.merge_pdfs([self._p(i) for i in task["inputs"]], self._p(task["output"]))
        if t == "watermark_pdf":
            return pdf_tasks.watermark_pdf(self._p(task["input"]), self._p(task["output"]), task.get("text", "CONFIDENTIAL"))
        if t == "generate_report":
            return word_tasks.generate_report(self._p(self.config["template"]), self._p(task["output"]), task["data"])
        if t == "extract_word_text":
            return word_tasks.extract_word_text(self._p(task["input"]), self._p(task["output"]))
        raise ValueError(f"Unknown task type: {t}")

    def run_all(self):
        for task in self.config["tasks"]:
            try:
                self._run(task)
                self.audit.append((task["type"], "SUCCESS", task.get("output", "")))
            except Exception as e:
                logger.error(f"Task {task['type']} failed: {e}")
                self.audit.append((task["type"], "FAILED", str(e)))
        return self.write_audit()

    def write_audit(self):
        reports = self._p(self.config["reports_dir"])
        ensure_dir(reports)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(reports, f"audit_report_{stamp}.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"Audit report generated {datetime.datetime.now().isoformat(timespec='seconds')}\n")
            for name, status, detail in self.audit:
                f.write(f"{status:8} {name:20} {detail}\n")
        logger.info(f"Audit report -> {path}")
        return path
