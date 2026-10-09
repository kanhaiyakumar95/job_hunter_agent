import sqlite3
import datetime
import json

DB_FILE = "jobs.db"

# Initializes SQLite tables for jobs and users, then triggers initial expired job cleanup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT,
            user_id TEXT,
            title TEXT,
            description TEXT,
            url TEXT,
            status TEXT,
            first_viewed TIMESTAMP,
            PRIMARY KEY (id, user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            hashed_password TEXT
        )
    ''')
    conn.commit()
    conn.close()
    cleanup_expired_jobs(30)

# Inserts a new username and hashed password into the users table
def create_user(username, hashed_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, hashed_password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Retrieves user account record by username for credential verification
def get_user_by_username(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, hashed_password FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "hashed_password": row[1]}
    return None

# Inserts a newly scraped job for a user if not already present in the database
def add_job(user_id, job_id, title, description, url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Insert if not exists
    c.execute('SELECT id FROM jobs WHERE id = ? AND user_id = ?', (job_id, user_id))
    if not c.fetchone():
        now = datetime.datetime.now().isoformat()
        c.execute('''
            INSERT INTO jobs (id, user_id, title, description, url, status, first_viewed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, user_id, title, description, url, "new", now))
    conn.commit()
    conn.close()

# Automatically deletes jobs older than the specified TTL (default 30 days) across the database
def cleanup_expired_jobs(days=30):
    """Automatically deletes jobs older than the specified TTL (default 30 days) across the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    c.execute('DELETE FROM jobs WHERE first_viewed < ?', (cutoff,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        print(f"🧹 [Auto-Cleanup] Purged {deleted} jobs older than {days} days.")
    return deleted

# Purges stale records and retrieves all unacted ('new') jobs for the authenticated user
def get_active_jobs(user_id):
    # Automatically enforce TTL cleanup
    cleanup_expired_jobs(30)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Fetch all "new" jobs for the specific user
    c.execute('SELECT id, title, description, url, first_viewed FROM jobs WHERE status = "new" AND user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    
    jobs = []
    for r in rows:
        jobs.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "url": r[3],
            "first_viewed": r[4]
        })
    return jobs

# Updates the user-specific state of a job to 'applied' or 'not_interested'
def update_job_status(user_id, job_id, status):
    # status can be "applied" or "not_interested"
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE jobs SET status = ? WHERE id = ? AND user_id = ?', (status, job_id, user_id))
    conn.commit()
    conn.close()

init_db()
