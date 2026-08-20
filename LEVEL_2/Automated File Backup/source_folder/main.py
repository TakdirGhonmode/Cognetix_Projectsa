import os
import time
import schedule

from monitor import start_monitor
from backup_manager import backup_file


SOURCE_FOLDER = "source_folder"
BACKUP_FOLDER = "backup_folder"


def scheduled_backup():
    """
    Backup all files from the source folder.
    """

    print("\nRunning Scheduled Backup...")

    for file in os.listdir(SOURCE_FOLDER):

        source_path = os.path.join(SOURCE_FOLDER, file)

        if os.path.isfile(source_path):

            backup_file(
                source_path,
                BACKUP_FOLDER
            )


if __name__ == "__main__":

    # Create folders if they don't exist
    os.makedirs(SOURCE_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    # Schedule automatic backup every 5 minutes
    schedule.every(5).minutes.do(scheduled_backup)

    print("=" * 50)
    print(" Automated File Backup & Versioning System ")
    print("=" * 50)
    print(f"Source Folder : {SOURCE_FOLDER}")
    print(f"Backup Folder : {BACKUP_FOLDER}")
    print("Monitoring Started...")
    print("=" * 50)

    # Start monitoring in a separate thread
    import threading

    monitor_thread = threading.Thread(
        target=start_monitor,
        args=(SOURCE_FOLDER, BACKUP_FOLDER),
        daemon=True
    )

    monitor_thread.start()

    # Keep checking the schedule
    while True:
        schedule.run_pending()
        time.sleep(1)