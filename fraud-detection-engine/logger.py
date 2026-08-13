import os
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import MySQLDatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AuditLogger")


class AuditLogger:
    """
    Maintains a strict audit trail for compliance tracking.
    Logs transaction audit records to:
    1. Text log file ('audit_log.txt')
    2. MySQL 'audit_logs' table (via database manager)
    """

    def __init__(self, log_filepath: str = "audit_log.txt", db_manager: Optional[MySQLDatabaseManager] = None):
        self.log_filepath = log_filepath
        self.db_manager = db_manager

    def log_evaluation_results(self, df_evaluated: pd.DataFrame) -> int:
        """
        Logs evaluation results for all processed transactions.
        Appends entries to 'audit_log.txt' and writes to MySQL database if connected.
        """
        logged_count = 0
        with open(self.log_filepath, "a", encoding="utf-8") as f:
            header_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n==================== AUDIT LOG BATCH RUN: {header_time} ====================\n")

            for idx, row in df_evaluated.iterrows():
                tx_id = str(row['Transaction ID'])
                user_id = str(row['User ID'])
                tx_date = row['Date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
                score = int(row.get('Risk Score', 0))
                level = str(row.get('Risk Level', 'LOW'))
                is_flagged = bool(row.get('Is Flagged', False))
                status = "FLAGGED" if is_flagged else "CLEARED"

                rules = row.get('Triggered Rules', [])
                rules_str = ", ".join(rules) if isinstance(rules, list) and rules else "NONE"

                log_entry = (
                    f"[{tx_date}] TX_ID: {tx_id} | USER: {user_id} | STATUS: {status} | "
                    f"RISK_SCORE: {score} ({level}) | TRIGGERED_RULES: [{rules_str}]\n"
                )

                f.write(log_entry)
                logged_count += 1

                # Log to MySQL if database connection is active
                if self.db_manager and self.db_manager.is_connected:
                    self.db_manager.insert_audit_log(
                        tx_id=tx_id,
                        timestamp=tx_date,
                        event_type="TRANSACTION_EVALUATION",
                        rules=rules_str,
                        risk_score=score,
                        status=status,
                        message=log_entry.strip()
                    )

        logger.info(f"Audit Logger: Successfully wrote {logged_count} entries to '{self.log_filepath}' and MySQL database.")
        return logged_count
