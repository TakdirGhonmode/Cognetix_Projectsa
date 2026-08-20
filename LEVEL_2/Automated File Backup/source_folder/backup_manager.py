import os
import shutil
import hashlib

from versioning import generate_version_name
from logger import log_backup, log_error


def calculate_hash(file_path):
    """
    Generate SHA256 hash for a file.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            data = file.read(4096)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


def is_duplicate(source_file, backup_folder):
    """
    Check whether a file with the same content
    already exists in the backup folder.
    """

    source_hash = calculate_hash(source_file)

    for file in os.listdir(backup_folder):

        backup_file = os.path.join(backup_folder, file)

        if os.path.isfile(backup_file):

            backup_hash = calculate_hash(backup_file)

            if backup_hash == source_hash:
                return True

    return False


def verify_integrity(original_file, copied_file):
    """
    Verify copied file by comparing hashes.
    """

    return calculate_hash(original_file) == calculate_hash(copied_file)


def backup_file(source_file, backup_folder):
    """
    Create versioned backup.
    """

    try:

        # Check duplicate
        if is_duplicate(source_file, backup_folder):

            print("Duplicate file detected. Backup skipped.")

            log_backup(
                os.path.basename(source_file),
                "-",
                "DUPLICATE"
            )

            return

        # Original filename
        file_name = os.path.basename(source_file)

        # Generate version name
        versioned_name, version = generate_version_name(
            file_name,
            backup_folder
        )

        # Destination path
        destination = os.path.join(
            backup_folder,
            versioned_name
        )

        # Copy file
        shutil.copy2(source_file, destination)

        # Verify integrity
        if verify_integrity(source_file, destination):

            print("Backup completed successfully.")

            log_backup(
                file_name,
                version,
                "SUCCESS"
            )

        else:

            print("Integrity verification failed.")

            log_error(
                file_name,
                "Integrity verification failed."
            )

    except Exception as e:

        print("Backup failed.")

        log_error(
            os.path.basename(source_file),
            str(e)
        )


if __name__ == "__main__":

    source = "source_folder/report.txt"
    backup = "backup_folder"

    os.makedirs("source_folder", exist_ok=True)
    os.makedirs("backup_folder", exist_ok=True)

    if not os.path.exists(source):
        with open(source, "w") as file:
            file.write("Hello Internship Project")

    backup_file(source, backup)