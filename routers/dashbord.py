from fastapi import APIRouter

import sys
sys.path.insert(0,'/storage/emulated/0/School management')

from database import get_connection

router = APIRouter(prefix='/dashboard', tags=['Dashboard'])

@router.get('/')
def get_dashboard():
    with get_connection() as conn:
        students_count = conn.execute('SELECT COUNT(*) as count FROM students WHERE is_active = 1').fetchone() ['count']
        
        teachers_count = conn.execute('SELECT COUNT(*) as count FROM teachers WHERE is_active = 1').fetchone() ['count']
        
        classes_count = conn.execute('SELECT COUNT(*) as count FROM classes').fetchone() ['count']
        
        subjects_count = conn.execute('SELECT COUNT(*) as count FROM subjects').fetchone() ['count']
        
        enrollments_count = conn.execute('SELECT COUNT(*) as count FROM student_enrollment WHERE exit_date IS NULL').fetchone() ['count']
        
        enrollments_by_year = conn.execute('''
        SELECT
            academic_years.year,
            COUNT(*) AS count
        FROM student_enrollment
        JOIN academic_years ON student_enrollment.academic_year_id = academic_years.id
        WHERE student_enrollment.exit_date IS NULL
        GROUP BY academic_years.year
        ORDER BY academic_years.year DESC
        ''').fetchall()
        
        students_by_class = conn.execute('''
        SELECT
            classes.class_name,
            COUNT(*) AS count
        FROM student_enrollment
        JOIN classes ON student_enrollment.class_id = classes.id
        WHERE student_enrollment.exit_date IS NULL
        GROUP BY classes.class_name
        ORDER BY classes.class_name
        ''').fetchall()
        
        return {
            'total': {
                'students': students_count,
                'teachers': teachers_count,
                'classes': classes_count,
                'subjects': subjects_count,
                'enrollments': enrollments_count
            },
                'enrollments_by_year': [dict(item)for item in enrollments_by_year],
                'students_by_class': [dict(item)for item in students_by_class]
        }