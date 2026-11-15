from fastapi import APIRouter, HTTPException, Depends
from routers.auth import get_current_user 
from pydantic import BaseModel, Field, ConfigDict

import sys
sys.path.insert(0,'/storage/emulated/0/School management')

from database import get_connection

router = APIRouter(prefix='/students', tags=['Students'])

class StudentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=50)
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=50)


@router.post('/')
def create_student(data: StudentCreate, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        existing = conn.execute(
            'SELECT id FROM students WHERE name = ? AND is_active = 1',
            (data.name,)
        ).fetchone()

        if existing:
            raise HTTPException(status_code=409, detail='Already exists')

      
        cursor = conn.execute('INSERT INTO students (name) VALUES (?)', (data.name,))
        new_student_id = cursor.lastrowid

        
        conn.execute('''
            INSERT INTO student_logins (student_id, username, password)
            VALUES (?, ?, ?)
        ''', (new_student_id, data.username, data.password))

        return {'message': 'Student Added'}
        
@router.get('/')
def get_students(current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        students = conn.execute('SELECT id, name, is_active FROM students WHERE is_active = 1 ORDER BY id'). fetchall()
        
        return [dict(student) for student in students]
        

@router.get('/{student_id}')
def get_student(student_id:int, current_user: dict =  Depends(get_current_user)):
    with get_connection() as conn:
        student = conn.execute('SELECT id, name, is_active FROM students WHERE id = ?',
        (student_id,)
        ).fetchone()
        
        if student is None:
            raise HTTPException(
            status_code=404,
            detail='Not found')
            
        return dict(student)
            
            
class UpdateStudent(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    
@router.put('/{student_id}')
def update_student(student_id:int, data: UpdateStudent, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        student = conn.execute('SELECT id FROM students WHERE id = ?',
        (student_id,)
        ).fetchone()
        
        if student is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        existing = conn.execute('SELECT id FROM students WHERE name = ? AND id != ? AND is_active = 1',
        (data.name, student_id)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail='Name already exists')
            
        conn.execute('UPDATE students SET name = ? WHERE id = ?',
        (data.name, student_id)
        )
        
        return {
            'message': 'Student updated'
        }
        
@router.delete('/{student_id}')
def remove_students(student_id: int, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        student = conn.execute('SELECT id FROM students WHERE id =?',
        (student_id,)
        ).fetchone()
        
        if student is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        conn.execute('UPDATE students SET is_active = 0 WHERE id =?',
        (student_id,)
        )

        return {
            'message': 'Student deactivated'
        }
        
        
@router.get('/me/enrollment')
def get_my_enrollment(current_user: dict = Depends(get_current_user)):
    # چک می‌کنیم که فقط دانش‌آموز بتونه از این استفاده کنه
    if current_user.get('role') != 'student':
        raise HTTPException(status_code=403, detail='Access denied')
    
    student_id = int(current_user.get('sub')) # آیدی دانش‌آموز از توکن

    with get_connection() as conn:
        enrollment = conn.execute('''
            SELECT id FROM student_enrollment 
            WHERE student_id = ? AND exit_date IS NULL
            LIMIT 1
        ''', (student_id,)).fetchone()

        if enrollment is None:
            raise HTTPException(status_code=404, detail='No active enrollment found')
            
        return {'enrollment_id': enrollment['id']}