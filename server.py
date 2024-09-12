from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

def get_db_connection():
    conn = sqlite3.connect('userinfo.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            count INTEGER NOT NULL,
            death_count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class UserStats(BaseModel):
    username: str
    count: int
    death_count: int

class RegisterData(BaseModel):
    nickname: str
    count: int

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/butter")
def read_butter():
    return FileResponse("butter.html")

@app.post("/register")
async def register(user_data: RegisterData):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM users WHERE username = ?", (user_data.nickname,))
        existing_user = cur.fetchone()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="닉네임이 중복됩니다!")
        
        cur.execute("""
            INSERT INTO users (username, count, death_count)
            VALUES (?, ?, ?)
        """, (user_data.nickname, 0, 0))  # death_count 기본값 0
        conn.commit()
        return {"message": "회원가입이 완료되었습니다!"}
    except sqlite3.Error as e:
        print(f"SQLite error on register: {e}")
        raise HTTPException(status_code=500, detail="서버에서 문제가 발생했습니다.")
    finally:
        conn.close()

@app.post("/update_stats")
async def update_stats(user_stats: UserStats):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM users WHERE username = ?", (user_stats.username,))
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다!")

        cur.execute("""
            UPDATE users
            SET count = ?, death_count = ?
            WHERE username = ?
        """, (user_stats.count, user_stats.death_count, user_stats.username))
        conn.commit()

        print(f"Updated stats for user: {user_stats.username}, count: {user_stats.count}, death_count: {user_stats.death_count}")  # 로그 추가
        return {"message": "유저 데이터가 업데이트되었습니다!"}
    except sqlite3.Error as e:
        print(f"SQLite error on update_stats: {e}")
        raise HTTPException(status_code=500, detail="서버에서 문제가 발생했습니다.")
    finally:
        conn.close()


@app.get("/get_user_stats")
async def get_user_stats(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT count, death_count FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다!")

        return {"count": user[0], "death_count": user[1]}
    except sqlite3.Error as e:
        print(f"SQLite error on get_user_stats: {e}")
        raise HTTPException(status_code=500, detail="서버에서 문제가 발생했습니다.")
    finally:
        conn.close()

@app.get("/get_rankings")
async def get_rankings():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT username, count, death_count
            FROM users
            ORDER BY death_count DESC, count DESC, username DESC
        """)
        rows = cur.fetchall()
        
        rankings = [{"username": row["username"], "count": row["count"], "death_count": row["death_count"]} for row in rows]
        
        return rankings
    except sqlite3.Error as e:
        print(f"SQLite error on get_rankings: {e}")
        raise HTTPException(status_code=500, detail="서버에서 문제가 발생했습니다.")
    finally:
        conn.close()
