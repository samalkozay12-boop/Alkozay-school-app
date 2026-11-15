from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

import sys
sys.path.insert(0,'/storage/emulated/0/School management')

from database import get_connection

router = APIRouter(prefix = '/academic-years', tags=['Academic Years'])

class AcademicYearCreate(BaseModel):
    year: int = Field(ge=1300, le=1500)
    
@router.post('/')
def create_academic_year(data:AcademicYearCreate):
    with get_connection() as conn:
        existing = conn.execute('SELECT id FROM academic_years WHERE year = ?',
        (data.year,)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail='Year already exists')
            
        conn.execute('INSERT INTO academic_years(year) VALUES(?)',
        (data.year,)
        )
        
        return {
            'message': 'Academic year created'
        }
        
@router.get('/')
def get_academic_year():
    with get_connection() as conn:
        years = conn.execute('SELECT id, year FROM academic_years ORDER BY year DESC').fetchall()
        
        return [dict(item)for item in years]
        
@router.get('/{year_id}')
def get_year_id(year_id:int):
    with get_connection() as conn:
        years = conn.execute('SELECT id, year FROM academic_years WHERE id = ?',
        (year_id,)
        ).fetchone()
        
        if years is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        return dict(years)
        
@router.delete('/{year_id}')
def remove_year(year_id:int):
    with get_connection() as conn:
        year = conn.execute('SELECT id FROM academic_years WHERE id = ?',
        (year_id,)
        ).fetchone()
        
        if year is None:
            raise HTTPException(status_code=404, detail='Not found')
            
        enrollment = conn.execute('SELECT id FROM student_enrollment WHERE academic_year_id = ?',
        (year_id,)
        ).fetchone()
        
        if enrollment:
            raise HTTPException(status_code=409, detail='Academic year has enrollments, cannot delete')
            
        conn.execute('DELETE FROM academic_years WHERE id = ?',
       (year_id,)
       )
       
        return {
           'message': 'academic year removed'
       }