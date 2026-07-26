import time
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backup_manager import backup_file


class FileMonitor(FileSystemEventHandler):

    def __init__(self, backup_folder):
        self.backup_folder = backup_folder

    def on_created(self, event):

        if event.is_directory:
            return

        print(f"\nNew File Detected : {event.src_path}")

        backup_file(
            event.src_path,
            self.backup_folder
        )

    def on_modified(self, event):

        if event.is_directory:
            return

        print(f"\nModified File : {event.src_path}")

        backup_file(
            event.src_path,
            self.backup_folder
        )


def start_monitor(source_folder, backup_folder):

    event_handler = FileMonitor(backup_folder)

    observer = Observer()

    observer.schedule(
        event_handler,
        source_folder,
        recursive=False
    )

    observer.start()

    print("=" * 50)
    print("Monitoring Started...")
    print(f"Source Folder : {source_folder}")
    print("=" * 50)

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        observer.stop()

        print("\nMonitoring Stopped.")

    observer.join()