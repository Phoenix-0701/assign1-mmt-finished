import sqlite3

def create_connection(db_file):
    """ Tạo kết nối đến file database SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Kết nối thành công đến {db_file} (SQLite v{sqlite3.sqlite_version})")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ Tạo bảng mới """
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS account (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_table)
        print("Đã tạo bảng (hoặc đã tồn tại).")
    except sqlite3.Error as e:
        print(e)

def insert_account(conn, account):
    """ Thêm một sinh viên mới vào bảng """
    sql = ''' INSERT INTO account(username,password)
              VALUES(?,?) '''
    try:
        cursor = conn.cursor()
        cursor.execute(sql, account)
        # conn.commit() # Chỉ commit khi thực sự muốn lưu
        return cursor.lastrowid # Trả về ID của sinh viên vừa thêm
    except sqlite3.IntegrityError:
        print(f"Lỗi: Username '{account[0]}' đã tồn tại.")
        return None

def select_user(conn,username):
    """ Truy vấn user bất kỳ """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM account WHERE username=?", (username,))

    return  cursor.fetchone() # Lấy kết quả
