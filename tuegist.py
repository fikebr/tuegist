from config import Config
import requests
import sqlite3
from datetime import datetime, timedelta
import logging
import os
from jinja2 import Environment, FileSystemLoader

cfg = Config()
log = logging.getLogger(__name__)

class TueGist:
    def __init__(self):
        self.db = DB()
        self.output_folder_path = cfg.output_folder_path
        
        # Setup Jinja environment
        templates_dir = os.path.join(cfg.base_dir, "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        
    def scan(self):
        log.info("Scanning Gists")

        gh = Github()
        gists = gh.query_gists()
        
        log.info(f"Found {len(gists)} gists")

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

        if os.path.exists(index_file_path):
            log.info("Index already exists")
            return
        
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

            db.create_gist(gist)

            gists.append({
                'url': gist['url'],
                'id': gist['id'], 
                'created_at': gist['created_at'],
                'updated_at': gist['updated_at'],
                'description': gist['description']
            })
            
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
            log.info(f"Gist {gist_data['id']} has not been modified since {existing_gist['modified_date']}")
            return

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

    def get_most_recent_tuesday(self, date: datetime):
        """Returns the date of the most recent Tuesday before the given date."""
        today = date
        # Calculate days to go back to reach the previous Tuesday
        # If today is Tuesday (1), we want to go back 7 days
        # If today is Wednesday (2), we want to go back 1 day
        # If today is Thursday (3), we want to go back 2 days, etc.
        days_back = ((today.weekday() - 1) % 7) or 7  # Use 7 if result is 0 (Tuesday)
        most_recent_tuesday = today - timedelta(days=days_back)
        return most_recent_tuesday

    def backfill_published_date(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, modified_date FROM gists WHERE published_date IS NULL OR published_date = ''")
            rows = cursor.fetchall()
            
            current_time = self.get_most_recent_tuesday(datetime.now())
            current_time_str = current_time.strftime('%Y-%m-%d')
            
            for row in rows:
                gist_id = row['id']
                
                cursor.execute("UPDATE gists SET published_date = ? WHERE id = ?", (current_time_str, gist_id))
                conn.commit()
                
                current_time = self.get_most_recent_tuesday(current_time)
                current_time_str = current_time.strftime('%Y-%m-%d')

        




