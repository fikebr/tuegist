"""Configuration settings for TueGist."""

import os

# Default configuration values
USERNAME = "fikebr"
LOGFILE = "tuegist.log"
OUTPUT_FOLDER = "www"
DB_FILE = "tuegist.db"

# Create absolute paths for files and folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGFILE_PATH = os.path.join(BASE_DIR, "logs", LOGFILE)
OUTPUT_FOLDER_PATH = os.path.join(BASE_DIR,  "..", OUTPUT_FOLDER)
DB_FILE_PATH = os.path.join(BASE_DIR, DB_FILE)

# Ensure output directory exists
os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)


