
# Automated File Backup & Versioning System

## Project Overview

This project automatically creates backups of files when they are changed. It stores different versions of files, avoids duplicate backups, and keeps a log of all backup activities.

## Features

- Monitor file changes
- Create automatic backups
- Store multiple file versions
- Skip duplicate backups
- Verify backup integrity using SHA-256
- Maintain backup logs

## Technologies Used

- Python 3
- os
- shutil
- hashlib
- logging
- datetime
- time

## Project Structure

```
Automated_File_Backup_System/
│── source_folder/
│── backup_folder/
│── logs/
│── main.py
│── backup.py
│── monitor.py
│── utils.py
│── README.md
```

## How to Run

1. Install Python 3.
2. Place the files you want to back up in the `source_folder`.
3. Run the program:
   ```bash
   python main.py
   ```
4. The program will monitor the folder and create backups automatically.

## Output

- Backup files are stored in `backup_folder`.
- Backup history is stored in `logs/backup.log`.

## Author

**Takdir Ghonmode**
