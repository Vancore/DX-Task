import sqlite3
import threading
import time

def connection_lock(func):
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return wrapper

class Database:
    def __init__ (self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.lock = threading.RLock()
        self.create_tables()

    #create
    @connection_lock
    def create_tables(self):
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY,  active_list_id INTEGER, last_msg_id INTEGER, prem INTEGER DEFAULT 0)""")
            try:
                self.conn.execute("ALTER TABLE users ADD COLUMN prem_until INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            self.conn.execute("UPDATE users SET prem_until = -1 WHERE prem = 1 AND prem_until = 0")
            self.conn.execute("""CREATE TABLE IF NOT EXISTS list (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT)""")
            self.conn.execute("""CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, list_id INTEGER, txt TEXT, done_val INTEGER DEFAULT 0)""")

    #add
    @connection_lock
    def add_user(self, uid):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    @connection_lock
    def add_list(self, uid, name):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO list (user_id, title) VALUES (?, ?)", (uid, name,))
            return cursor.lastrowid
    @connection_lock
    def add_task(self, lid, text):
        with self.conn:
            self.conn.execute("INSERT INTO tasks (list_id, txt) VALUES (?, ?)", (lid, text,))

    #get
    @connection_lock
    def get_active_list(self, uid):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT active_list_id FROM users WHERE user_id = ?", (uid,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
    @connection_lock
    def get_all_list(self, uid):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, title FROM list WHERE user_id = ?", (uid,))
            return cursor.fetchall()
    @connection_lock
    def get_tasks(self, lid):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, txt, done_val FROM tasks WHERE list_id = ?", (lid,))
            return cursor.fetchall()
    @connection_lock
    def get_list_title(self, lid):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT title FROM list WHERE id = ?", (lid,))
            row = cursor.fetchone()
            if row:
                return row[0]
            else:
                return "List not found"
    @connection_lock
    def get_last_msg(self, uid):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT last_msg_id FROM users WHERE user_id = ?", (uid,))
            row = cursor.fetchone()
            if row and row[0] is not None:
                return row[0]
            return None

    #count
    @connection_lock
    def count_lists(self, uid):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM list WHERE user_id = ?", (uid,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return 0
    @connection_lock
    def count_tasks(self, lid):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE list_id = ?", (lid,))
        row = cursor.fetchone()
        return row[0] if row else 0
    @connection_lock
    def count_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

    #update
    @connection_lock
    def set_active_list(self, uid, lid):
            with self.conn:
                self.conn.execute("UPDATE users SET active_list_id = ? WHERE user_id = ?", (lid, uid,))
    @connection_lock
    def update_last_msg(self, uid, mid):
        with self.conn:
            self.conn.execute("UPDATE users SET last_msg_id = ? WHERE user_id = ?", (mid, uid,))
    @connection_lock
    def done_task(self, tid):
        with self.conn:
            self.conn.execute("UPDATE tasks SET done_val = 1 - done_val WHERE id = ?", (tid,))
            cursor = self.conn.cursor()
            cursor.execute("SELECT done_val FROM tasks WHERE id = ?", (tid,))
            row = cursor.fetchone()
            return row[0] if row else 0

    #delete
    @connection_lock
    def delete_task(self, tid):
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (tid,))
    @connection_lock
    def rem_list(self, uid, lid):
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE list_id = ? AND list_id IN (SELECT id FROM list WHERE user_id = ?)", (lid, uid))
            self.conn.execute("UPDATE users SET active_list_id = NULL WHERE active_list_id = ? AND user_id = ?", (lid, uid))
            self.conn.execute("DELETE FROM list WHERE id = ? AND user_id = ?", (lid, uid))

    #premium
    @connection_lock
    def is_premium(self, uid):
        cursor = self.conn.cursor()
        cursor.execute("SELECT prem, prem_until FROM users WHERE user_id = ?", (uid,))
        row = cursor.fetchone()
        if not row:
            return 0
        prem, prem_until = row
        if prem == 1 or prem_until == -1:
            return 1
        if prem_until and prem_until > int(time.time()):
            return 1
        return 0
    @connection_lock
    def set_pro(self, uid, days=-1):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
            cursor = self.conn.cursor()
            cursor.execute("SELECT prem_until FROM users WHERE user_id = ?", (uid,))
            row = cursor.fetchone()
            current_until = row[0] if row and row[0] else 0
            if days == -1 or current_until == -1:
                self.conn.execute("UPDATE users SET prem = 1, prem_until = -1 WHERE user_id = ?", (uid,))
            else:
                now = int(time.time())
                base_time = max(now, current_until)
                new_until = base_time + (days * 86400)
                self.conn.execute("UPDATE users SET prem = 0, prem_until = ? WHERE user_id = ?", (new_until, uid,))

    @connection_lock
    def get_pro_info(self, uid):
        """Возвращает текстовый статус подписки для UI"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT prem, prem_until FROM users WHERE user_id = ?", (uid,))
        row = cursor.fetchone()
        if not row:
            return "Free"
        prem, prem_until = row
        if prem == 1 or prem_until == -1:
            return "Lifetime 👑"
        now = int(time.time())
        if prem_until and prem_until > now:
            date_str = time.strftime('%d.%m.%Y', time.localtime(prem_until))
            return f"Active until {date_str} ⏳"
        return "Free"
    
    @connection_lock
    def get_premium_users(self):
        cursor = self.conn.cursor()
        now = int(time.time())
        cursor.execute("SELECT COUNT(*) FROM users WHERE prem = 1 OR prem_until = -1 OR prem_until > ?", (now,))
        return cursor.fetchone()[0]

db = Database("data.db")
            
