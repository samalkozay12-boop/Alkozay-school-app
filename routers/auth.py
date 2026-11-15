from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sys

sys.path.insert(0, '/storage/emulated/0/School management')
from database import get_connection
from security import create_access_token, decode_access_token

router = APIRouter(prefix='/auth', tags=['Authentication'])
security_scheme = HTTPBearer()

class LoginData(BaseModel):
    username: str
    password: str

@router.post('/login')
def user_login(data: LoginData):
    with get_connection() as conn:
        # ۱. چک کردن مدیر
        admin = conn.execute(
            'SELECT id, username FROM admins WHERE username = ? AND password = ?',
            (data.username, data.password)
        ).fetchone()

        if admin:
            token = create_access_token({'sub': admin['username'], 'role': 'admin'})
            return {'access_token': token, 'token_type': 'bearer', 'role': 'admin', 'username': admin['username']}

        # ۲. چک کردن دانش‌آموز
        student = conn.execute('''
            SELECT student_login.student_id, students.name 
            FROM student_login
            JOIN students ON student_login.student_id = students.id
            WHERE student_login.username = ? AND student_login.password = ?
        ''', (data.username, data.password)).fetchone()

        if student:
            token = create_access_token({'sub': str(student['student_id']), 'role': 'student'})
            return {'access_token': token, 'token_type': 'bearer', 'role': 'student', 'username': str(student['student_id'])}

        # ۳. چک کردن معلم
        teacher = conn.execute('''
            SELECT teacher_logins.teacher_id, teachers.name 
            FROM teacher_logins
            JOIN teachers ON teacher_logins.teacher_id = teachers.id
            WHERE teacher_logins.username = ? AND teacher_logins.password = ?
        ''', (data.username, data.password)).fetchone()

        if teacher:
            token = create_access_token({'sub': str(teacher['teacher_id']), 'role': 'teacher'})
            return {'access_token': token, 'token_type': 'bearer', 'role': 'teacher', 'username': str(teacher['teacher_id'])}

        raise HTTPException(status_code=401, detail='نام کاربری یا رمز عبور اشتباه است')


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail='توکن نامعتبر یا منقضی شده است')
    return payload