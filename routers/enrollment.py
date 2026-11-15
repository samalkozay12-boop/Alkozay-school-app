from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import sys
sys.path.insert(0,'/storage/emulated/0/School management')

from database import get_connection

router = APIRouter(prefix= '/enrollment', tags=['Enrollment'])

class EnrollmentCreate(BaseModel):
    student_id: int
    academic_year_id: int
    class_id: int
    enrollment_date: str
    
@router.post('/')
def create_enrollment(data:EnrollmentCreate):
    with get_connection()as conn:
        student = conn.execute('SELECT id FROM students WHERE id = ? AND is_active=1',
        (data.student_id,)
        ).fetchone()
        
        if student is None:
            raise HTTPException(status_code=404, detail='Student not found')
            
        year = conn.execute('SELECT id FROM academic_years WHERE id =?',
        (data.academic_year_id,)
        ).fetchone()
        
        if year is None:
            raise HTTPException(status_code=404, detail='Academic year not found')
            
        cls = conn.execute('SELECT id FROM classes WHERE id = ?',
        (data.class_id,)
        ).fetchone()
        
        if cls is None:
            raise HTTPException(status_code=404, detail='Class not found')
            
        existing = conn.execute('SELECT id FROM student_enrollment WHERE student_id = ? AND academic_year_id = ? AND exit_date IS NULL',
        (data.student_id, data.academic_year_id)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail= 'Student already enrolled in this academic year')
            
        conn.execute('INSERT INTO student_enrollment (student_id, academic_year_id, class_id, enrollment_date) VALUES(?,?,?,?)',
        (data.student_id, data.academic_year_id, data.class_id, data.enrollment_date)
        )
        
        return {
            'message': 'Enrollment created'
        }
        
@router.get('/')
def get_enrollment():
    with get_connection() as conn:
        enrollments = conn.execute('''
        SELECT
            student_enrollment.id,
            students.name AS student_name,
            academic_years.year AS academic_year,
            classes.class_name,
            student_enrollment.enrollment_date,
            student_enrollment.exit_date
            
        FROM student_enrollment
        JOIN students ON student_enrollment.student_id = students.id
        JOIN academic_years ON student_enrollment.academic_year_id = academic_years.id
        JOIN classes ON student_enrollment.class_id = classes.id
        ORDER BY student_enrollment.id DESC
        ''').fetchall()
        
        return [dict(item)for item in enrollments]
        
@router.get('/student/{student_id}')
def get_student_enrollments(student_id: int):
    with get_connection() as conn:
        enrollments = conn.execute('''
        SELECT
            student_enrollment.id,
            academic_years.year AS academic_year,
            classes.class_name,
            student_enrollment.enrollment_date,
            student_enrollment.exit_date
        FROM student_enrollment
        JOIN academic_years ON student_enrollment.academic_year_id = academic_years.id
        JOIN classes ON student_enrollment.class_id = classes.id
        WHERE student_enrollment.student_id = ?
        ORDER BY academic_years.year DESC
        ''',(student_id,)
        ).fetchall()
        
        return [dict(item)for item in enrollments]
        
 
@router.delete('/{enrollment_id}')
def remove_enrollment(enrollment_id: int):
    with get_connection() as conn:
        enrollments = conn.execute('SELECT id FROM student_enrollment WHERE id = ?',
        (enrollment_id,)
        ).fetchone()
        
        if enrollments is None:
            raise HTTPException(status_code=404, detail= 'Not found')
            
        conn.execute('DELETE FROM exam_results WHERE enrollment_id = ?',
        (enrollment_id,)
        )
        
        conn.execute('DELETE FROM student_enrollment WHERE id = ?',
        (enrollment_id,)
        )
        
        return {
            'message': 'Enrollment_removed'
        }