import pandas as pd
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AlertManager")


class AlertManager:
    """
    Handles structured alert generation and formatted console rendering
    for flagged suspicious transactions.
    """

    # ANSI Color Codes for terminal formatting
    COLOR_RED = "\033[91m"
    COLOR_YELLOW = "\033[93m"
    COLOR_GREEN = "\033[92m"
    COLOR_CYAN = "\033[96m"
    COLOR_BOLD = "\033[1m"
    COLOR_RESET = "\033[0m"

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def generate_console_alerts(self, flagged_df: pd.DataFrame) -> List[str]:
        """
        Formats and prints real-time structured alerts to the console for flagged transactions.
        Returns a list of formatted alert message strings.
        """
        alerts = []
        if flagged_df.empty:
            print(f"{self.COLOR_GREEN}[INFO] No suspicious transactions detected in dataset.{self.COLOR_RESET}")
            return alerts

        header = f"\n{self.COLOR_BOLD}{'='*80}\n [FRAUD MONITORING ENGINE] REAL-TIME TRANSACTION ALERTS DETECTED\n{'='*80}{self.COLOR_RESET}"
        print(header)

        for idx, row in flagged_df.iterrows():
            tx_id = row['Transaction ID']
            user_id = row['User ID']
            amt = row['Transaction Amount']
            date_str = row['Date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
            loc = row['Location']
            score = row['Risk Score']
            level = row['Risk Level']
            rules = row['Triggered Rules']
            rules_str = ", ".join(rules) if isinstance(rules, list) else str(rules)

            if level == "HIGH":
                badge = f"{self.COLOR_RED}{self.COLOR_BOLD}[ALERT - HIGH RISK ({score}/100)]{self.COLOR_RESET}"
            elif level == "MEDIUM":
                badge = f"{self.COLOR_YELLOW}{self.COLOR_BOLD}[WARN - MEDIUM RISK ({score}/100)]{self.COLOR_RESET}"
            else:
                badge = f"{self.COLOR_CYAN}[NOTICE - LOW RISK ({score}/100)]{self.COLOR_RESET}"

            msg = (
                f"{badge}\n"
                f"  |-- Transaction ID: {self.COLOR_BOLD}{tx_id}{self.COLOR_RESET} | User: {user_id}\n"
                f"  |-- Amount: ${amt:,.2f} | Date: {date_str} | Location: {loc}\n"
                f"  +-- Triggered Rules: {self.COLOR_BOLD}{rules_str}{self.COLOR_RESET}\n"
            )
            print(msg)
            alerts.append(msg)

        footer = f"{self.COLOR_BOLD}{'='*80}\n Total Suspicious Alerts Generated: {len(flagged_df)}\n{'='*80}{self.COLOR_RESET}\n"
        print(footer)

        logger.info(f"Generated {len(alerts)} console alerts.")
        return alerts
