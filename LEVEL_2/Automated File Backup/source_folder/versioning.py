import os
from datetime import datetime


def generate_version_name(file_name, backup_folder):
    """
    Generate a versioned filename.

    Example:
    report.txt
        ↓
    report_v1_2026-07-25_15-30-20.txt
    """

    name, extension = os.path.splitext(file_name)

    version = 1

    # Check existing backups
    for existing_file in os.listdir(backup_folder):
        if existing_file.startswith(name + "_v"):
            version += 1

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    versioned_file = f"{name}_v{version}_{timestamp}{extension}"

    return versioned_file, version
if __name__ == "__main__":

    backup_folder = "backup_folder"

    os.makedirs(backup_folder, exist_ok=True)

    filename, version = generate_version_name(
        "report.txt",
        backup_folder
    )

    print(filename)
    print(version)