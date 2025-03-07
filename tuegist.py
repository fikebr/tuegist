from config import Config
import requests
import sqlite3
from datetime import datetime, timedelta
import logging
import os
from jinja2 import Environment, FileSystemLoader
import subprocess

cfg = Config()
log = logging.getLogger(__name__)


def get_the_tuesday_before_date(self, date: datetime) -> datetime:
    """Returns the date of the most recent Tuesday before the given date."""
    days_back = ((date.weekday() - 1) % 7) or 7  # Use 7 if result is 0 (Tuesday)
    most_recent_tuesday = date - timedelta(days=days_back)
    return most_recent_tuesday


def get_the_tuesday_after_date(date: datetime) -> datetime:
    """Returns the date of the most recent Tuesday after the given date."""
    days_back = ((date.weekday() + 1) % 7) or 7  # Use 7 if result is 0 (Tuesday)
    most_recent_tuesday = date + timedelta(days=days_back)
    return most_recent_tuesday

def is_date_a_tuesday(date: datetime) -> bool:
    """Returns True if the given date is a Tuesday, False otherwise."""
    return date.weekday() == 1

def datestring_to_datetime(datestring: str) -> datetime:
    """Converts a date string to a datetime object."""
    return datetime.strptime(datestring, '%Y-%m-%d')

def datetime_to_datestring(datetime: datetime) -> str:
    """Converts a datetime object to a date string."""
    return datetime.strftime('%Y-%m-%d')



class TueGist:
    def __init__(self):
        self.db = DB()
        self.output_folder_path = cfg.output_folder_path
        
        # Setup Jinja environment
        templates_dir = os.path.join(cfg.base_dir, "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        
    def tues(self):
        log.info("Performing Weekly Post Actions")

        self.scan()
        
        # Get the most recent Tuesday
        most_recent_published_date = self.db.most_recent_published_date()
        most_recent_published_date = datestring_to_datetime(most_recent_published_date)

        next_tuesday = get_the_tuesday_after_date(most_recent_published_date)
        
        tuesdays = []
        
        while next_tuesday <= datetime.now():
            tuesdays.append(next_tuesday)
            next_tuesday = get_the_tuesday_after_date(next_tuesday)
            
        gists_published = 0
        for tuesday in tuesdays:
            next_gist_id = self.db.get_next_post_id()
            
            if next_gist_id:
                self.db.set_published_date(next_gist_id, datetime_to_datestring(tuesday))
                gists_published += 1
                
        if gists_published > 0:
            self.build_gists()
            self.build_index()
            commit_message = f"Published {gists_published} new gists on {datetime_to_datestring(datetime.now())}"
            self.git_commit_output_folder(commit_message)
            log.info(commit_message)
        
    def git_commit_output_folder(self, commit_message: str):
        log.info("Committing Output Folder")
        

        # Change to the repository directory
        original_dir = os.getcwd()
        os.chdir(cfg.output_folder_path)
        
        try:
            # Git commit
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f'"{commit_message}"'], check=True)
            
            # Git push
            subprocess.run(['git', 'push'], check=True)
        
        finally:
            # Change back to original directory
            os.chdir(original_dir)
        
        
    def scan(self):
        log.info("Scanning Github for Gists")

        gh = Github()
        gists = gh.query_gists()
        
        # log.info(f"Found {len(gists)} gists")

    def rebuild(self):
        log.info("Rebuilding Everything")

        gists_folder_path = os.path.join(self.output_folder_path, "gists")
        if os.path.exists(gists_folder_path):
            for file in os.listdir(gists_folder_path):
                if file.endswith('.html'):
                    os.remove(os.path.join(gists_folder_path, file))

        if os.path.exists(self.output_folder_path):
            for file in os.listdir(self.output_folder_path):
                if file.endswith('.html'):
                    os.remove(os.path.join(self.output_folder_path, file))


        self.scan()
        self.db.backfill_published_date()
        self.build_index()
        self.build_pages()
        self.build_gists()
    
    
    def build_index(self):
        log.info("Building Index Files")
        
        # Building index.html
        index_file_path = os.path.join(self.output_folder_path, "index.html")
        
        gists = self.db.get_gists_all()

        template = self.jinja_env.get_template("index.jinja")
        html_content = template.render(gists=gists, cfg=cfg)

        with open(index_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Building categories.html & tags.html
        
        categories = {}
        tags = {}
        category_count = {}
        tag_count = {}
        
        for gist in gists:
            if gist['category'] not in categories:
                categories[gist['category']] = []
                category_count[gist['category']] = 0
            categories[gist['category']].append(gist)
            category_count[gist['category']] += 1
            
            if gist['tags'] == "":
                if "no-tag" not in tags:
                    tags["no-tag"] = []
                    tag_count["no-tag"] = 0
                tags["no-tag"].append(gist)
                tag_count["no-tag"] += 1
                continue
            
            gist_tags = gist['tags'].split(', ')  # Renamed from tags to gist_tags
            for tag in gist_tags:
                if tag not in tags:  # Using tags_dict instead of tags
                    tags[tag] = []
                    tag_count[tag] = 0
                tags[tag].append(gist)
                tag_count[tag] += 1
            
                
        category_list = sorted(category_count.keys(), key=lambda x: category_count[x], reverse=True)
        tag_list = sorted(tag_count.keys(), key=lambda x: tag_count[x], reverse=True)
        
        template = self.jinja_env.get_template("categories.jinja")
        html_content = template.render(categories=categories, category_list=category_list, category_count=category_count, cfg=cfg)
        
        with open(os.path.join(self.output_folder_path, "categories.html"), 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        template = self.jinja_env.get_template("tags.jinja")
        html_content = template.render(tags=tags, tag_list=tag_list, tag_count=tag_count, cfg=cfg)
        
        with open(os.path.join(self.output_folder_path, "tags.html"), 'w', encoding='utf-8') as f:
            f.write(html_content)
            
            
            
            
            
    def build_pages(self):
        log.info("Building Pages")

        pages = ['about', 'contact']

        for page in pages:
            file_path = os.path.join(self.output_folder_path, f"{page}.html")
            
            template = self.jinja_env.get_template(f"{page}.jinja")
            html_content = template.render(cfg=cfg)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

    def build_gists(self):
        log.info("Building All Gists")

        gists = self.db.get_gists_all()
        for gist in gists:
            html_file_path = os.path.join(self.output_folder_path, "gists", f"{gist['id']}.html")

            if os.path.exists(html_file_path):
                log.info(f"Gist {gist['id']} already exists")
                continue
            
            self.build_gist(gist['id'])

    def build_gist(self, gist_id: str):
        gist = self.db.get_gist(gist_id)

        if not gist:
            log.error(f"Gist {gist_id} not found")
            return
        
        html_file_path = os.path.join(self.output_folder_path, "gists", f"{gist['id']}.html")

        if os.path.exists(html_file_path):
            log.info(f"Gist {gist['id']} already exists")
            return
        
        # Get template and render
        template = self.jinja_env.get_template("gist.jinja")
        html_content = template.render(gist=gist, cfg=cfg)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
        
        # Write the rendered HTML to file
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        log.info(f"Built HTML for gist {gist['id']}")

class Github:
    def __init__(self):
        self.username = cfg.username
    
    def query_gists(self) -> list:
        
        
        response = requests.get(f"https://api.github.com/users/{self.username}/gists")
        if not response.ok:
            log.error(f"Failed to fetch gists: {response.status_code}")
            return []
            
        gists = []
        
        db = DB()
        for gist in response.json():

            gist['created_at'] = datetime.strptime(gist['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M')
            gist['updated_at'] = datetime.strptime(gist['updated_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M')

            created = 0
            updated = 0

            result = db.create_gist(gist)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1

            gists.append({
                'url': gist['url'],
                'id': gist['id'], 
                'created_at': gist['created_at'],
                'updated_at': gist['updated_at'],
                'description': gist['description']
            })
            
        log.info(f"{len(gists)} gists found, {created} created, {updated} updated")
        return gists


class DB:
    def __init__(self):
        """Initialize database connection and ensure tables exist."""
        self.db_path = self._validate_db_file(cfg.db_file_path)
        self.conn = None
        
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        
    def _validate_db_file(self, db_path: str) -> str:
        if not os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE gists (
                        id TEXT PRIMARY KEY,
                        description TEXT,
                        create_date TIMESTAMP,
                        modified_date TIMESTAMP,
                        published_date TIMESTAMP,
                        tags TEXT,
                        summary TEXT
                    )
                ''')
                conn.commit()
                log.info(f"Created new database file at {db_path}")
                
        return db_path
    
    def parse_description(self, description: str) -> dict:
        """Parse the description of a gist into a title, category, tags dictionary."""
        parts = description.split(": ", 1)
        
        if len(parts) == 2:
            category = parts[0]
            title = parts[1]
        else:
            category = ""
            title = description
            
        # Extract tags from end of title
        tags = []
        words = title.split()
        
        # Work backwards from end to find hashtags
        while words and words[-1].startswith('#'):
            tag = words.pop()[1:] # Remove the # prefix
            tags.append(tag)
            
        # Reconstruct title without the tags
        title = ' '.join(words)
            
        return {
            "category": category,
            "title": title,
            "tags": ", ".join(tags) if tags else ""
        }



    def create_gist(self, gist_data):
        existing_gist = self.get_gist(gist_data['id'])
        
        if existing_gist and existing_gist['modified_date'] >= gist_data['updated_at']:
            # log.info(f"Gist {gist_data['id']} has not been modified since {existing_gist['modified_date']}")
            return(None)

        result = "updated" if existing_gist else "created"
        
        parsed_description = self.parse_description(gist_data['description'])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO gists 
                (id, description, category, tags, summary, create_date, modified_date, published_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                gist_data['id'],
                parsed_description['title'],
                parsed_description['category'],
                parsed_description['tags'],
                gist_data['description'],
                gist_data['created_at'],
                gist_data['updated_at'],
                ""
            ))
            conn.commit()
            log.info(f"Gist {gist_data['id']} saved to database")
            
            return(result)

    def get_gist(self, gist_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, description, category, tags, summary, create_date, modified_date, published_date FROM gists WHERE id = ?", (gist_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_gists_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            sql = """SELECT id, description, category, tags, summary, create_date, modified_date, published_date
            FROM gists
            WHERE published_date IS NOT NULL
            ORDER BY published_date DESC"""

            cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_next_post_id(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id 
                FROM gists 
                WHERE published_date IS NULL OR published_date = ''
                ORDER BY modified_date DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            id = row['id'] if row else None
            
            if id:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                cursor.execute("UPDATE gists SET published_date = ? WHERE id = ?", (current_time, id))
                conn.commit()
                log.info(f"Updated published_date to {current_time} for gist {id}")
            
            return id

    def set_published_date(self, gist_id: str, published_date: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE gists SET published_date = ? WHERE id = ?", (published_date, gist_id))
            conn.commit()

    def backfill_published_date(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, modified_date FROM gists WHERE published_date IS NULL OR published_date = ''")
            rows = cursor.fetchall()
            
            current_time = get_the_tuesday_before_date(datetime.now())
            current_time_str = current_time.strftime('%Y-%m-%d')
            
            for row in rows:
                gist_id = row['id']
                
                cursor.execute("UPDATE gists SET published_date = ? WHERE id = ?", (current_time_str, gist_id))
                conn.commit()
                
                current_time = get_the_tuesday_before_date(current_time)
                current_time_str = current_time.strftime('%Y-%m-%d')

    def most_recent_published_date(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(published_date) as published_date FROM gists")
            row = cursor.fetchone()
            if not row or row['published_date'] is None:
                return ""
            return row['published_date']
        




