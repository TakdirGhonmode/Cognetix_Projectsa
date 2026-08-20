import logging

logging.basicConfig(
    filename="backup_logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def log_backup(file_name, version, status):
    """
    Log successful or skipped backup.
    """
    logging.info(
        f"File: {file_name} | Version: {version} | Status: {status}"
    )


def log_error(file_name, error):
    """
    Log backup errors.
    """
    logging.error(
        f"File: {file_name} | Error: {error}"
    )