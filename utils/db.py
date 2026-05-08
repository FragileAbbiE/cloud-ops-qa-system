import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join("data", "app.db")

def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL DEFAULT 'engineer',
        created_at TEXT,
        last_login TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_token TEXT UNIQUE NOT NULL,
        created_at TEXT,
        expires_at TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query TEXT,
        answer TEXT,
        source_file TEXT,
        sources_json TEXT,
        similarity_score REAL,
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        product_line TEXT,
        component TEXT,
        doc_type TEXT,
        file_path TEXT,
        file_size INTEGER,
        uploaded_by INTEGER,
        uploaded_at TEXT
    )
    """)


    # 产品线配置表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 组件配置表（关联产品线，级联删除）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_line_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_line_id) REFERENCES product_lines(id) ON DELETE CASCADE,
        UNIQUE(product_line_id, name)
    )
    """)

    # 文档类型配置表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS doc_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 默认产品线
    cur.execute("SELECT COUNT(*) FROM product_lines")
    if cur.fetchone()[0] == 0:
        default_pls = [
            ("K8s_Container", "Kubernetes 容器编排"),
            ("Ceph_Storage", "Ceph 分布式存储"),
            ("Network", "网络基础设施"),
            ("Database", "数据库系统"),
            ("Linux_OS", "Linux 操作系统"),
        ]
        cur.executemany("INSERT INTO product_lines (name, description) VALUES (?, ?)", default_pls)

    # 默认文档类型
    cur.execute("SELECT COUNT(*) FROM doc_types")
    if cur.fetchone()[0] == 0:
        default_dts = ["故障排障", "部署指南", "运维手册", "最佳实践", "FAQ"]
        cur.executemany("INSERT INTO doc_types (name) VALUES (?)", [(t,) for t in default_dts])

    # 默认组件
    cur.execute("SELECT COUNT(*) FROM components")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id, name FROM product_lines")
        pl_map = {row[1]: row[0] for row in cur.fetchall()}

        default_comps = []
        if "K8s_Container" in pl_map:
            for comp in ["Pod", "Deployment", "Service", "Ingress", "ConfigMap"]:
                default_comps.append((pl_map["K8s_Container"], comp))
        if "Ceph_Storage" in pl_map:
            for comp in ["OSD", "Monitor", "MDS", "RGW"]:
                default_comps.append((pl_map["Ceph_Storage"], comp))
        if "Network" in pl_map:
            for comp in ["VPC", "LoadBalancer", "Firewall", "DNS"]:
                default_comps.append((pl_map["Network"], comp))
        if "Database" in pl_map:
            for comp in ["MySQL", "PostgreSQL", "Redis", "MongoDB"]:
                default_comps.append((pl_map["Database"], comp))
        if "Linux_OS" in pl_map:
            for comp in ["Kernel", "Systemd", "Network_Stack", "Filesystem"]:
                default_comps.append((pl_map["Linux_OS"], comp))

        if default_comps:
            cur.executemany("INSERT INTO components (product_line_id, name) VALUES (?, ?)", default_comps)

    conn.commit()
    conn.close()

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_user(username: str, password_hash: str, email: str, role: str = "engineer"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(username,password_hash,email,role,created_at,is_active) VALUES(?,?,?,?,?,1)",
        (username, password_hash, email, role, now_str()),
    )
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def list_users() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role, created_at, last_login, is_active FROM users ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_last_login(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_login=? WHERE id=?", (now_str(), user_id))
    conn.commit()
    conn.close()

def set_user_active(user_id: int, active: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active=? WHERE id=?", (active, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def create_session(user_id: int, token: str, expires_at: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions(user_id,session_token,created_at,expires_at,is_active) VALUES(?,?,?,?,1)",
        (user_id, token, now_str(), expires_at),
    )
    conn.commit()
    conn.close()

def get_session(token: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sessions WHERE session_token=? AND is_active=1", (token,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def deactivate_session(token: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE sessions SET is_active=0 WHERE session_token=?", (token,))
    conn.commit()
    conn.close()

def add_audit_log(user_id: int, query: str, answer: str, docs: List[Dict[str, Any]]):
    source_file = docs[0]["source_file"] if docs else None
    score = docs[0]["score"] if docs else None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO audit_log(user_id,query,answer,source_file,sources_json,similarity_score,timestamp)
           VALUES(?,?,?,?,?,?,?)""",
        (user_id, query, answer, source_file, json.dumps(docs, ensure_ascii=False), score, now_str()),
    )
    conn.commit()
    conn.close()

def list_audit_logs(username: str = "", start_time: str = "", end_time: str = "") -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    sql = """
    SELECT a.id, u.username, a.query, a.answer, a.source_file, a.similarity_score, a.timestamp
    FROM audit_log a
    LEFT JOIN users u ON a.user_id = u.id
    WHERE 1=1
    """
    params = []
    if username:
        sql += " AND u.username LIKE ?"
        params.append(f"%{username}%")
    if start_time:
        sql += " AND a.timestamp >= ?"
        params.append(start_time)
    if end_time:
        sql += " AND a.timestamp <= ?"
        params.append(end_time)
    sql += " ORDER BY a.id DESC"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_document_record(filename: str, file_path: str, file_size: int, uploaded_by: int,
                        product_line: str = "", component: str = "", doc_type: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO documents(filename,product_line,component,doc_type,file_path,file_size,uploaded_by,uploaded_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (filename, product_line, component, doc_type, file_path, file_size, uploaded_by, now_str()),
    )
    conn.commit()
    conn.close()

def list_documents() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def delete_document(doc_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM documents WHERE id=?", (doc_id,))
    row = cur.fetchone()
    if row and row["file_path"] and os.path.exists(row["file_path"]):
        os.remove(row["file_path"])
    cur.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


def update_user(user_id: int, email: str = None, password_hash: str = None, role: str = None):
    conn = get_conn()
    cur = conn.cursor()

    updates = []
    params = []

    if email is not None:
        updates.append("email=?")
        params.append(email)
    if password_hash is not None:
        updates.append("password_hash=?")
        params.append(password_hash)
    if role is not None:
        updates.append("role=?")
        params.append(role)

    if not updates:
        conn.close()
        return

    params.append(user_id)
    sql = f"UPDATE users SET {', '.join(updates)} WHERE id=?"
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def get_connection():
    return get_conn()


# ========== 产品线管理 ==========
def list_product_lines():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, created_at FROM product_lines ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "created_at": r[3]} for r in rows]

def add_product_line(name: str, description: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO product_lines (name, description) VALUES (?, ?)", (name, description))
    conn.commit()
    conn.close()

def delete_product_line(pl_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_lines WHERE id = ?", (pl_id,))
    conn.commit()
    conn.close()

# ========== 组件管理 ==========
def list_components(product_line_id: int = None):
    conn = get_connection()
    cursor = conn.cursor()
    if product_line_id:
        cursor.execute("""
            SELECT c.id, c.name, p.name as product_line, p.id as pl_id
            FROM components c JOIN product_lines p ON c.product_line_id = p.id
            WHERE c.product_line_id = ? ORDER BY c.name
        """, (product_line_id,))
    else:
        cursor.execute("""
            SELECT c.id, c.name, p.name as product_line, p.id as pl_id
            FROM components c JOIN product_lines p ON c.product_line_id = p.id
            ORDER BY p.name, c.name
        """)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "product_line": r[2], "product_line_id": r[3]} for r in rows]

def add_component(product_line_id: int, name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO components (product_line_id, name) VALUES (?, ?)", (product_line_id, name))
    conn.commit()
    conn.close()

def delete_component(comp_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM components WHERE id = ?", (comp_id,))
    conn.commit()
    conn.close()

# ========== 文档类型管理 ==========
def list_doc_types():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM doc_types ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "created_at": r[2]} for r in rows]

def add_doc_type(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO doc_types (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def delete_doc_type(dt_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doc_types WHERE id = ?", (dt_id,))
    conn.commit()
    conn.close()

