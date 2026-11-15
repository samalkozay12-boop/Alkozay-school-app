from fastapi import APIRouter, HTTPException, Depends
from routers.auth import get_current_user
from pydantic import BaseModel, Field, ConfigDict

import sys
sys.path.insert(0,'/storage/emulated/0/School management')

from database import get_connection

router = APIRouter(prefix='/teachers', tags = ['Teachers'])


class TeacherCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    
@router.post('/')
def create_teacher(data:TeacherCreate, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        existing = conn.execute('SELECT name FROM teachers WHERE name = ? AND is_active = 1',
        (data.name,)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail='Already exists')
        
        
        conn.execute('INSERT INTO teachers(name) VALUES(?)',
        (data.name,)
        )
        
        return {
            'message': 'teacher added'
        }
        
@router.get('/')
def get_teachers(current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        teachers = conn.execute('SELECT id, name, is_active FROM teachers WHERE is_active = 1 ORDER BY id').fetchall()
        
        return [dict(teacher) for teacher in teachers]
        
@router.get('/{teacher_id}')
def get_teacher(teacher_id: int, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        teacher = conn.execute('SELECT id, name, is_active FROM teachers WHERE id =?',
        (teacher_id,)
        ).fetchone()
        
        if teacher is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        return dict(teacher)
        
class UpdateTeacher(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=50)
    
@router.put('/{teacher_id}')
def teacher_update(teacher_id: int, data: UpdateTeacher, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        teacher = conn.execute('SELECT id FROM teachers WHERE id=?',
        (teacher_id,)
        ).fetchone()
        
        if teacher is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        existing = conn.execute('SELECT id FROM teachers WHERE name = ? AND id != ? AND is_active=1',
        (data.name, teacher_id)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail='Name already exists')
            
        conn.execute('UPDATE teachers SET name =? WHERE id =?',
        (data.name, teacher_id)
        )
        
        return {
            'message': 'teacher updated'
        }
        
@router.delete('/{teacher_id}')
def remove_teacher(teacher_id:int, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        teacher = conn.execute('SELECT id FROM teachers WHERE id = ?',
        (teacher_id,)
        ).fetchone()
        
        if teacher is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        conn.execute('UPDATE teachers SET is_active = 0 WHERE id = ?',
        (teacher_id,)
        )
  
        return {
            'message': 'teacher deactivated'
        }
        