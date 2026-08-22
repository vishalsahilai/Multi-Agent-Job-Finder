import csv
import io
from datetime import datetime
from typing import Optional


#  Status Constants 

STATUS_APPLIED   = "Applied"
STATUS_FAILED    = "Failed"
STATUS_MANUAL    = "Manual Required"
STATUS_SKIPPED   = "Skipped"
STATUS_CAPTCHA   = "Captcha Detected"


#  Logger Class 

class ApplicationLogger:
    """
    In-memory log of all application attempts.
    No database — just a list of dicts held in RAM.
    """

    def __init__(self):
        self.entries = []

    def log(
        self,
        job_url:   str,
        title:     str,
        company:   str,
        board:     str,
        status:    str,
        note:      Optional[str] = None,
    ) -> dict:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title":     title,
            "company":   company,
            "board":     board,
            "status":    status,
            "note":      note or "",
            "job_url":   job_url,
        }
        self.entries.append(entry)
        return entry

    def summary(self) -> dict:
        total    = len(self.entries)
        applied  = sum(1 for e in self.entries if e["status"] == STATUS_APPLIED)
        failed   = sum(1 for e in self.entries if e["status"] == STATUS_FAILED)
        manual   = sum(1 for e in self.entries if e["status"] == STATUS_MANUAL)
        captcha  = sum(1 for e in self.entries if e["status"] == STATUS_CAPTCHA)
        skipped  = sum(1 for e in self.entries if e["status"] == STATUS_SKIPPED)

        return {
            "total":   total,
            "applied": applied,
            "failed":  failed,
            "manual":  manual,
            "captcha": captcha,
            "skipped": skipped,
        }

    def to_csv(self) -> str:
        if not self.entries:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=[
            "timestamp", "title", "company", "board",
            "status", "note", "job_url"
        ])
        writer.writeheader()
        writer.writerows(self.entries)
        return buf.getvalue()

    def clear(self):
        self.entries = []