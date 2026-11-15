from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
import sqlite3
import sys

sys.path.insert(0, '/storage/emulated/0/School management')
from database import get_connection

router = APIRouter(prefix='/classes', tags=['Classes'])

class ClassCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    class_name: str = Field(min_length=2, max_length=50)
    teacher_id: int

@router.post('/')
def create_class(data: ClassCreate):
    with get_connection() as conn:
        teacher = conn.execute('SELECT id FROM teachers WHERE id = ? AND is_active = 1', (data.teacher_id,)).fetchone()
        if teacher is None:
            raise HTTPException(status_code=404, detail='Teacher not found')
            
        existing = conn.execute('SELECT id FROM classes WHERE class_name = ?', (data.class_name,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail='Class already exists')
            
        conn.execute('INSERT INTO classes(teacher_id, class_name) VALUES(?,?)', (data.teacher_id, data.class_name))
        return {'message': 'class created'}

@router.get('/')
def get_classes():
    with get_connection() as conn:
        classes = conn.execute("""
            SELECT classes.id, classes.class_name, teachers.name AS teacher_name
            FROM classes
            JOIN teachers ON classes.teacher_id = teachers.id
            WHERE teachers.is_active=1
            ORDER BY classes.class_name
        """).fetchall()
        
        # اینجا از JSONResponse استفاده می‌کنیم که استانداردترین راهه
        return JSONResponse(content=[dict(item) for item in classes])

@router.get('/{class_id}')
def get_class_id(class_id: int):
    with get_connection() as conn:
        cls = conn.execute("""
            SELECT classes.id, classes.class_name, teachers.name AS teacher_name
            FROM classes
            JOIN teachers ON classes.teacher_id = teachers.id
            WHERE classes.id = ?
        """, (class_id,)).fetchone()
        
        if cls is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        return JSONResponse(content=dict(cls))

class UpdateClass(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    class_name: str = Field(min_length=2, max_length=50)
    teacher_id: int

@router.put('/{class_id}')
def update_class(class_id: int, data: UpdateClass):
    with get_connection() as conn:
        cls = conn.execute('SELECT id FROM classes WHERE id = ?', (class_id,)).fetchone()
        if cls is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        teacher = conn.execute('SELECT id FROM teachers WHERE id = ? AND is_active = 1', (data.teacher_id,)).fetchone()
        if teacher is None:
            raise HTTPException(status_code=404, detail='Teacher not found')
            
        existing = conn.execute('SELECT id FROM classes WHERE class_name = ? AND id != ?', (data.class_name, class_id)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail='Class name already exists')
            
        conn.execute('UPDATE classes SET class_name = ?, teacher_id = ? WHERE id = ?', (data.class_name, data.teacher_id, class_id))
        return {'message': 'class updated'}

@router.delete('/{class_id}')
def remove_class(class_id: int):
    with get_connection() as conn:
        cls = conn.execute('SELECT id FROM classes WHERE id = ?', (class_id,)).fetchone()
        if cls is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        enrollment = conn.execute('SELECT id FROM student_enrollment WHERE class_id = ? AND exit_date IS NULL', (class_id,)).fetchone()
        if enrollment:
            raise HTTPException(status_code=409, detail='Class has active students, cannot delete')
            
        conn.execute('DELETE FROM classes WHERE id = ?', (class_id,))
        return {'message': 'class removed'}
        
@router.get('/{class_id}/students')
def get_class_students(class_id: int):
    with get_connection() as conn:
        # پیدا کردن دانش‌آموزانی که تو این صنف (و سال تحصیلی فعال) ثبت‌نام کردن
        students = conn.execute('''
            SELECT
                student_enrollment.id AS enrollment_id,
                students.id AS student_id,
                students.name AS student_name
            FROM student_enrollment
            JOIN students ON student_enrollment.student_id = students.id
            WHERE student_enrollment.class_id = ? AND student_enrollment.exit_date IS NULL
            ORDER BY students.name
        ''', (class_id,)).fetchall()

        return [dict(s) for s in students]