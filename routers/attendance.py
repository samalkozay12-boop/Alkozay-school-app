from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

import sys
sys.path.insert(0,'/storage/emulated/0/School management')

from database import get_connection
from routers.auth import get_current_user

router = APIRouter(prefix='/attendance', tags=['Attendance'])

class AttendanceData(BaseModel):
    enrollment_id: int
    date: str
    status: str
    
@router.post('/')
def mark_attendance(data: AttendanceData, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        existing = conn.execute('SELECT id FROM attendance WHERE enrollment_id = ? AND date = ?',
        (data.enrollment_id, data.date)
        ).fetchone()
        
        if existing:
            conn.execute('UPDATE attendance SET status = ? WHERE id = ?',
            (data.status, existing['id'])
            )
            
            return {
                'message': 'attendance updated'
            }
            
        else:
            conn.execute('INSERT INTO attendance(enrollment_id, status, date) VALUES(?,?,?)',
            (data.enrollment_id, data.status, data.date)
            )
            
            return {
                'message': 'attendance updated'
            }
            

@router.get('/class/{class_id}/date/{date}')
def get_class_attendance(class_id: int, date: str, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        # لیست دانش‌آموزان این صنف و وضعیت حضور در آن تاریخ
        records = conn.execute('''
            SELECT 
                student_enrollment.id AS enrollment_id,
                students.name AS student_name,
                attendance.status,
                attendance.date
            FROM student_enrollment
            JOIN students ON student_enrollment.student_id = students.id
            LEFT JOIN attendance ON attendance.enrollment_id = student_enrollment.id AND attendance.date = ?
            WHERE student_enrollment.class_id = ? AND student_enrollment.exit_date IS NULL
            ORDER BY students.name
        ''', (date, class_id)).fetchall()
        
        return [dict(r) for r in records]