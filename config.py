import os

# Default configuration values
USERNAME = "fikebr"
LOGFILE = "tuegist.log"
OUTPUT_FOLDER = "www"
DB_FILE = "tuegist.db"
URL_BASE = "https://www.tuegist.com"
GITHUB_REPO = "https://github.com/fikebr/tuegist"

# Create absolute paths for files and folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))



class Config:
    def __init__(self):
        self.username = USERNAME
        self.logfile = LOGFILE
        self.output_folder = OUTPUT_FOLDER
        self.db_file = DB_FILE
        self.base_dir = BASE_DIR
        self.logfile_path = os.path.join(self.base_dir, "logs", LOGFILE)
        self.output_folder_path = self._get_output_folder_path()
        self.db_file_path = os.path.join(self.base_dir, self.db_file)
        self.url_base = URL_BASE
        self.github_repo = GITHUB_REPO

    def _get_output_folder_path(self):
        path = os.path.join(BASE_DIR,  "..", OUTPUT_FOLDER)
        os.makedirs(path, exist_ok=True)
        return path

