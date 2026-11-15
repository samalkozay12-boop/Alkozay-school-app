from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import sqlite3

import sys
sys.path.insert(0, '/storage/emulated/0/School management')

from database import get_connection

router = APIRouter(prefix = '/subjects', tags=['Subjects'])

class CreateSubject(BaseModel):
    name:str
    
@router.post('/')
def create_subject(data:CreateSubject):
    with get_connection() as conn:
        try:
            conn.execute('INSERT INTO subjects(name) VALUES (?)',
            (data.name,)
            )
            
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail='subject already exist')
             
        return {
            'message': 'subject added'
         }
         
@router.get('/')
def get_subjects():
    with get_connection() as conn:
        subjects = conn.execute('SELECT * FROM subjects ORDER BY id'
        ).fetchall()
        
        return [dict(subject)for subject in subjects]
        
        

@router.put('/{subject_id}')
def subject_update(subject_id: int, data: CreateSubject):
    with get_connection() as conn:
        subject = conn.execute('SELECT id FROM subjects WHERE id =?',
        (subject_id,)
        ).fetchone()
        
        if subject is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        try:
            conn.execute('UPDATE subjects SET name = ? WHERE id = ?',
            (data.name, subject_id)
            )
            
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail='Already exist')
            
        return {
            'message': 'subject updated'
        }
        
@router.delete('/{subject_id}')
def remove_subject(subject_id: int):
    with get_connection() as conn:
        subject = conn.execute('SELECT id FROM subjects WHERE id =?',
        (subject_id,)
        ).fetchone()
        
        if subject is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        
        conn.execute('DELETE FROM subjects WHERE id = ?',
        (subject_id,)
        )
        
        return {
            'message': 'subject removed'
        }