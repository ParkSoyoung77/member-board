import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
import pymysql

app = FastAPI()

load_dotenv()

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

# 디자인 수정을 위해 CSS 경로를 전체 URL로 잡았습니다.
HTML_HEAD = """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SY & YS CLOUD SERVICE</title>
    <link rel="stylesheet" href="https://www.sy99.cloud/style.css">
</head>
"""

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

            // 수정 로직을 실제 페이지 이동으로 변경했습니다.
            function editPost(postId) {{
                const pw = prompt("수정하려면 비밀번호를 입력하세요.");
                if(pw) {{
                    location.href=`/board/edit?id=${{postId}}&password=${{pw}}`;
                }}
            }}
        </script>
    </body></html>
    """

# 4. 수정 화면 (GET) - 새로 추가됨!
@app.get("/board/edit", response_class=HTMLResponse)
async def edit_page(id: int, password: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
            post = cursor.fetchone()
    finally: conn.close()

    if not post:
        return "글을 찾을 수 없습니다."
    
    if post['password'] != password:
        return "<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>"

    return f"""
    <html>{HTML_HEAD}<body>{NAV_BAR}
        <div class="content-card">
            <h2>✏️ 글 수정하기</h2>
            <form action="/board/edit" method="post">
                <input type="hidden" name="id" value="{id}">
                <input type="hidden" name="original_password" value="{password}">
                <input type="text" name="title" value="{post['title']}" required>
                <textarea name="content" rows="10" required>{post['content']}</textarea>
                <p style="font-size: 0.8rem; color: #666;">* 비밀번호는 수정할 수 없습니다.</p>
                <button type="submit" class="btn btn-primary" style="width: 100%; padding: 15px;">수정 완료</button>
            </form>
            <a href="/board/view?id={id}" class="btn btn-secondary" style="margin-top: 10px; width: 100%; text-align: center;">취소</a>
        </div>
    </body></html>
    """

# 5. 수정 처리 (POST) - 새로 추가됨!
@app.post("/board/edit")
async def do_edit(id: int = Form(...), title: str = Form(...), content: str = Form(...), original_password: str = Form(...)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 보안을 위해 비밀번호 재확인 후 업데이트합니다.
            cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s AND password=%s", 
                           (title, content, id, original_password))
        conn.commit()
    finally: conn.close()
    return HTMLResponse(f"<script>alert('수정되었습니다!'); location.href='/board/view?id={id}';</script>")

# 6. 저장 로직 (POST)
@app.post("/board/write")
async def do_write(title: str = Form(...), content: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO posts (title, content, password) VALUES (%s, %s, %s)", (title, content, password))
        conn.commit()
    finally: conn.close()
    return HTMLResponse("<script>alert('게시글이 등록되었습니다!'); location.href='/board/list';</script>")

# 7. 삭제 로직 (DELETE)
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