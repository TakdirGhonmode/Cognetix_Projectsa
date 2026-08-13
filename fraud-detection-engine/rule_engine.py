import pandas as pd
import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RuleEngine")


class BaseFraudRule(ABC):
    """
    Abstract Base Class for all modular fraud detection rules.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        """
        Evaluates rule against the DataFrame.
        Returns a boolean pandas Series (True = rule triggered/suspicious).
        """
        pass


class HighAmountRule(BaseFraudRule):
    """
    Rule 1: High Amount Threshold
    Flags transactions exceeding the configured max threshold amount.
    """

    def __init__(self):
        super().__init__(
            name="HighAmountRule",
            description="Transaction amount exceeds the high-risk threshold limit."
        )

    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        threshold = config.get("rules", {}).get("high_amount_threshold", 5000.0)
        return df["Transaction Amount"] > threshold


class RapidVelocityRule(BaseFraudRule):
    """
    Rule 2: Rapid Velocity / High-Frequency Activity
    Flags transactions when a user executes multiple transactions within a short time interval.
    """

    def __init__(self):
        super().__init__(
            name="RapidVelocityRule",
            description="High frequency of transactions from the same User ID within a short time window."
        )

    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        window_mins = config.get("rules", {}).get("velocity_time_window_minutes", 15)
        max_count = config.get("rules", {}).get("velocity_max_count", 3)

        triggered = pd.Series(False, index=df.index)

        # Group by User ID and evaluate rolling window frequency
        for user_id, group in df.groupby("User ID"):
            if len(group) < max_count:
                continue

            # Sort group by Date
            sorted_group = group.sort_values("Date")
            dates = sorted_group["Date"].values

            # Calculate frequency within window
            for i in range(len(sorted_group)):
                current_time = dates[i]
                window_start = current_time - np.timedelta64(window_mins, 'm')
                # Count transactions in window
                count_in_window = np.sum((dates >= window_start) & (dates <= current_time))
                if count_in_window > max_count:
                    original_idx = sorted_group.index[i]
                    triggered.loc[original_idx] = True

        return triggered


class GeographicalAnomalyRule(BaseFraudRule):
    """
    Rule 3: Geographical Anomaly / Unusual Locations
    Flags transactions originating from unusual locations or impossible speed location jumps between consecutive transactions.
    """

    def __init__(self):
        super().__init__(
            name="GeographicalAnomalyRule",
            description="Transactions from unusual regions or rapid geographical position shifts."
        )

    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        blacklisted_locations = set(config.get("rules", {}).get("blacklisted_locations", []))
        triggered = pd.Series(False, index=df.index)

        # 1. Direct location blacklist check
        blacklist_mask = df["Location"].isin(blacklisted_locations)
        triggered = triggered | blacklist_mask

        # 2. Check for rapid location jumps per user within 1 hour
        for user_id, group in df.groupby("User ID"):
            if len(group) < 2:
                continue

            sorted_group = group.sort_values("Date")
            prev_location = None
            prev_time = None

            for idx, row in sorted_group.iterrows():
                curr_location = row["Location"]
                curr_time = row["Date"]

                if prev_location is not None and curr_location != prev_location:
                    time_diff_hours = (curr_time - prev_time).total_seconds() / 3600.0
                    # Impossible travel: location changed in less than 1 hour
                    if time_diff_hours < 1.0:
                        triggered.loc[idx] = True

                prev_location = curr_location
                prev_time = curr_time

        return triggered


class FailedPaymentRule(BaseFraudRule):
    """
    Rule 4: Repeated Failed Payment Attempts
    Flags transactions where a user has repeated failed payment attempts or status anomalies.
    """

    def __init__(self):
        super().__init__(
            name="FailedPaymentRule",
            description="Repeated failed payment attempts detected prior to transaction."
        )

    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        max_failed = config.get("rules", {}).get("failed_payment_max_attempts", 2)
        triggered = pd.Series(False, index=df.index)

        # Check if 'Status' column exists
        if "Status" not in df.columns:
            return triggered

        # Direct failed status or cumulative failed count per user
        failed_mask = df["Status"].astype(str).str.upper() == "FAILED"
        triggered = triggered | failed_mask

        for user_id, group in df.groupby("User ID"):
            sorted_group = group.sort_values("Date")
            consecutive_failed = 0
            for idx, row in sorted_group.iterrows():
                status = str(row.get("Status", "SUCCESS")).upper()
                if status == "FAILED":
                    consecutive_failed += 1
                else:
                    if consecutive_failed >= max_failed:
                        triggered.loc[idx] = True
                    consecutive_failed = 0

        return triggered


class BlacklistRule(BaseFraudRule):
    """
    Rule 5: Blacklisted Accounts & Entities
    Flags transactions involving blacklisted User IDs, IP/Locations, or Payment Methods.
    """

    def __init__(self):
        super().__init__(
            name="BlacklistRule",
            description="Transaction matches blacklisted User ID or Payment Method."
        )

    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        blacklisted_users = set(config.get("rules", {}).get("blacklisted_user_ids", []))
        blacklisted_payments = set(config.get("rules", {}).get("blacklisted_payment_methods", []))

        user_mask = df["User ID"].isin(blacklisted_users)
        payment_mask = df["Payment Method"].isin(blacklisted_payments)

        return user_mask | payment_mask


class SpikeDetectionRule(BaseFraudRule):
    """
    Rule 6: Spike Detection / Value Anomaly
    Flags transactions where amount significantly exceeds the user's historical average (Z-score anomaly).
    """

    def __init__(self):
        super().__init__(
            name="SpikeDetectionRule",
            description="Sudden spike in transaction value compared to historical user average."
        )

    def evaluate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.Series:
        z_threshold = config.get("rules", {}).get("spike_zscore_threshold", 2.5)
        triggered = pd.Series(False, index=df.index)

        # Overall average fallback
        global_mean = df["Transaction Amount"].mean()
        global_std = df["Transaction Amount"].std()

        for user_id, group in df.groupby("User ID"):
            amounts = group["Transaction Amount"]
            if len(amounts) >= 3:
                user_mean = amounts.mean()
                user_std = amounts.std()
                if user_std > 0:
                    z_scores = (amounts - user_mean) / user_std
                    spike_indices = group.index[z_scores > z_threshold]
                    triggered.loc[spike_indices] = True
            else:
                # For users with < 3 transactions, test against global mean
                if global_std > 0:
                    for idx in group.index:
                        amt = df.loc[idx, "Transaction Amount"]
                        if (amt - global_mean) / global_std > z_threshold:
                            triggered.loc[idx] = True

        return triggered


class RuleEngine:
    """
    Orchestrates execution of all predefined modular fraud detection rules.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: List[BaseFraudRule] = [
            HighAmountRule(),
            RapidVelocityRule(),
            GeographicalAnomalyRule(),
            FailedPaymentRule(),
            BlacklistRule(),
            SpikeDetectionRule()
        ]

    def evaluate_all(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.Series]]:
        """
        Evaluates all registered rules against the transaction DataFrame.
        Returns:
            df_with_flags: DataFrame with boolean columns for each rule.
            rule_results: Dict mapping rule name to boolean Series.
        """
        logger.info(f"Evaluating {len(self.rules)} fraud detection rules across {len(df)} transactions...")
        rule_results = {}
        df_out = df.copy()

        for rule in self.rules:
            series = rule.evaluate(df_out, self.config)
            rule_results[rule.name] = series
            df_out[f"rule_{rule.name}"] = series
            triggered_count = series.sum()
            logger.info(f"Rule [{rule.name}]: Flagged {triggered_count} transactions.")

        return df_out, rule_results
