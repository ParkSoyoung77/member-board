import os
from dotenv import load_dotenv # .env 파일 로드를 위해 필요
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
import pymysql

app = FastAPI()

# .env 파일 읽기 (이게 실행되어야 os.getenv가 작동해요)
load_dotenv()

# 환경 변수 사용
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "db": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# 공통 헤더: VPC 1의 Nginx가 서빙하는 style.css를 참조합니다.
HTML_HEAD = """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SY & YS CLOUD SERVICE</title>
    <link rel="stylesheet" href="/style.css">
</head>
"""

# 공통 네비게이션 바: 모든 페이지 상단에 노출됩니다.
NAV_BAR = """
<nav class="navbar">
    <div class="navbar-container">
        <a href="/" class="nav-logo">SY & YS CLOUD</a>
        <div class="nav-links">
            <a href="/board/list">게시판목록</a>
            <a href="/board/write">글쓰기</a>
            <a href="/management/members">회원관리</a>
        </div>
    </div>
</nav>
"""

# 1. 글쓰기 화면 (GET)
@app.get("/board/write", response_class=HTMLResponse)
async def write_page():
    return f"""
    <html>{HTML_HEAD}<body>{NAV_BAR}
        <div class="content-card">
            <h2>✍️ 새 글 작성</h2>
            <form action="/board/write" method="post">
                <input type="text" name="title" placeholder="제목을 입력하세요" required>
                <textarea name="content" rows="10" placeholder="내용을 입력하세요" required></textarea>
                <input type="password" name="password" placeholder="수정/삭제 비밀번호" required>
                <button type="submit" class="btn btn-primary" style="width: 100%; padding: 15px;">등록하기</button>
            </form>
            <a href="/board/list" class="btn btn-secondary" style="margin-top: 10px; width: 100%; text-align: center;">목록으로 돌아가기</a>
        </div>
    </body></html>
    """

# 2. 목록 보기 (GET)
@app.get("/board/list", response_class=HTMLResponse)
async def list_page():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, created_at FROM posts ORDER BY id DESC")
            posts = cursor.fetchall()
    finally: conn.close()
    
    rows = "".join([f"<tr><td>{p['id']}</td><td><a href='/board/view?id={p['id']}'>{p['title']}</a></td><td>{p['created_at'].strftime('%Y-%m-%d')}</td></tr>" for p in posts])
    
    return f"""
    <html>{HTML_HEAD}<body>{NAV_BAR}
        <div class="content-card">
            <h2>📋 게시글 목록</h2>
            <table>
                <thead><tr><th>번호</th><th>제목</th><th>날짜</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div style="margin-top:20px;">
                <a href="/board/write" class="btn btn-primary">글쓰기</a>
                <a href="/" class="btn btn-secondary">홈으로</a>
            </div>
        </div>
    </body></html>
    """

# 3. 상세 보기 (GET)
@app.get("/board/view", response_class=HTMLResponse)
async def view_page(id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
            post = cursor.fetchone()
    finally: conn.close()
    
    if not post: return "해당 글이 존재하지 않습니다."
    
    return f"""
    <html>{HTML_HEAD}<body>{NAV_BAR}
        <div class="content-card">
            <h2 style="border-bottom: 2px solid #eee; padding-bottom: 10px;">{post['title']}</h2>
            <p style="white-space: pre-wrap; min-height: 250px; background: #fafafa; padding: 20px; border-radius: 8px;">{post['content']}</p>
            <div style="margin-top: 30px; display: flex; gap: 10px;">
                <a href="/board/list" class="btn btn-secondary">목록으로</a>
                <button class="btn btn-danger" onclick="deletePost({id})">삭제하기</button>
                <button class="btn" style="background: #ffc107; color: #000;" onclick="editPost({id})">수정하기</button>
            </div>
        </div>

        <script>
            function deletePost(postId) {{
                const pw = prompt("비밀번호를 입력하세요.");
                if(pw) {{
                    fetch(`/board/delete?id=${{postId}}&password=${{pw}}`, {{ method: 'DELETE' }})
                    .then(res => res.json())
                    .then(data => {{
                        alert(data.message);
                        if(data.message === "삭제 완료") location.href='/board/list';
                    }});
                }}
            }}

            function editPost(postId) {{
                const pw = prompt("비밀번호를 입력하세요.");
                if(pw) {{
                    alert("비밀번호 확인 완료! 수정 기능을 준비 중입니다.");
                }}
            }}
        </script>
    </body></html>
    """

# 4. 저장 로직 (POST)
@app.post("/board/write")
async def do_write(title: str = Form(...), content: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO posts (title, content, password) VALUES (%s, %s, %s)", (title, content, password))
        conn.commit()
    finally: conn.close()
    return HTMLResponse("<script>alert('게시글이 등록되었습니다!'); location.href='/board/list';</script>")

# 5. 삭제 로직 (DELETE)
@app.delete("/board/delete")
async def do_delete(id: int, password: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password FROM posts WHERE id = %s", (id,))
            post = cursor.fetchone()
            if post and post['password'] == password:
                cursor.execute("DELETE FROM posts WHERE id = %s", (id,))
                conn.commit()
                return {"message": "삭제 완료"}
            else:
                return {"message": "비밀번호가 일치하지 않습니다."}
    finally: conn.close()