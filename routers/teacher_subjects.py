from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys

sys.path.insert(0, '/storage/emulated/0/School management')
from database import get_connection

router = APIRouter(prefix='/teacher-subjects', tags=['Teacher Subjects'])

class AssignData(BaseModel):
    teacher_id: int
    subject_id: int
    class_id: int

@router.post('/')
def assign_teacher(data: AssignData):
    with get_connection() as conn:
        try:
            conn.execute('''
                INSERT INTO teacher_subjects (teacher_id, subject_id, class_id)
                VALUES (?, ?, ?)
            ''', (data.teacher_id, data.subject_id, data.class_id))
            return {'message': 'Assigned successfully'}
        except Exception as e:
            raise HTTPException(status_code=409, detail='این تخصیص از قبل وجود دارد')

@router.get('/teacher/{teacher_id}')
def get_teacher_assignments(teacher_id: int):
    with get_connection() as conn:
        assignments = conn.execute('''
            SELECT 
                classes.id AS class_id,
                classes.class_name,
                subjects.id AS subject_id,
                subjects.name AS subject_name
            FROM teacher_subjects
            JOIN classes ON teacher_subjects.class_id = classes.id
            JOIN subjects ON teacher_subjects.subject_id = subjects.id
            WHERE teacher_subjects.teacher_id = ?
        ''', (teacher_id,)).fetchall()
        return [dict(a) for a in assignments]

# برای حذف تخصیص (اگه اشتباه شد)
@router.delete('/{assignment_id}')
def remove_assignment(assignment_id: int):
    with get_connection() as conn:
        conn.execute('DELETE FROM teacher_subjects WHERE id = ?', (assignment_id,))
        return {'message': 'Removed'}