from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal
import sqlite3

import sys
sys.path.insert(0, '/storage/emulated/0/School management')

from database import get_connection
from routers.auth import get_current_user

router = APIRouter(prefix='/results', tags=['Results'])

class ResultCreate(BaseModel):
    enrollment_id: int
    subject_id: int
    exam_type: Literal['midyear', 'annual']
    score: int = Field(ge=0, le=60)

@router.post('/')
def create_result(data: ResultCreate, current_user: dict = Depends(get_current_user)):
    if data.exam_type == 'midyear' and data.score > 40:
        raise HTTPException(status_code=400, detail='Midyear maximum is 40')

    with get_connection() as conn:
        enr = conn.execute('SELECT id FROM student_enrollment WHERE id = ? AND exit_date IS NULL', (data.enrollment_id,)).fetchone()
        if enr is None:
            raise HTTPException(status_code=404, detail='Enrollment not found or inactive')

        subj = conn.execute('SELECT id FROM subjects WHERE id = ?', (data.subject_id,)).fetchone()
        if subj is None:
            raise HTTPException(status_code=404, detail='Subject not found')

        existing = conn.execute('SELECT id FROM exam_results WHERE enrollment_id = ? AND subject_id = ? AND exam_type = ?', (data.enrollment_id, data.subject_id, data.exam_type)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail='Result already exists for this exam type')

        conn.execute('''
            INSERT INTO exam_results (enrollment_id, subject_id, exam_type, score)
            VALUES (?, ?, ?, ?)
        ''', (data.enrollment_id, data.subject_id, data.exam_type, data.score))

        return {'message': 'Score added'}

@router.get('/')
def get_results(current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        results = conn.execute('''
            SELECT
                exam_results.id,
                students.name AS student_name,
                subjects.name AS subject_name,
                classes.class_name,
                academic_years.year AS academic_year,
                exam_results.exam_type,
                exam_results.score
            FROM exam_results
            JOIN student_enrollment ON exam_results.enrollment_id = student_enrollment.id
            JOIN students ON student_enrollment.student_id = students.id
            JOIN classes ON student_enrollment.class_id = classes.id
            JOIN academic_years ON student_enrollment.academic_year_id = academic_years.id
            JOIN subjects ON exam_results.subject_id = subjects.id
            ORDER BY exam_results.id DESC
        ''').fetchall()

        return [dict(r) for r in results]

@router.get('/class/{class_id}/subject/{subject_id}')
def get_class_subject_results(class_id: int, subject_id: int, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        results = conn.execute('''
            SELECT 
                exam_results.id AS result_id,
                exam_results.exam_type,
                exam_results.score,
                students.name AS student_name,
                student_enrollment.id AS enrollment_id
            FROM exam_results
            JOIN student_enrollment ON exam_results.enrollment_id = student_enrollment.id
            JOIN students ON student_enrollment.student_id = students.id
            WHERE student_enrollment.class_id = ? AND exam_results.subject_id = ?
            ORDER BY students.name
        ''', (class_id, subject_id)).fetchall()
        
        return [dict(r) for r in results]

class UpdateResult(BaseModel):
    score: int = Field(ge=0, le=60)

@router.put('/{result_id}')
def update_result(result_id: int, data: UpdateResult, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        result = conn.execute('SELECT id, exam_type FROM exam_results WHERE id = ?', (result_id,)).fetchone()

        if result is None:
            raise HTTPException(status_code=404, detail='Not found')

        if result['exam_type'] == 'midyear' and data.score > 40:
            raise HTTPException(status_code=400, detail='Midyear maximum is 40')

        conn.execute('UPDATE exam_results SET score = ? WHERE id = ?', (data.score, result_id))

        return {'message': 'Result updated'}

@router.delete('/{result_id}')
def remove_result(result_id: int, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        result = conn.execute('SELECT id FROM exam_results WHERE id = ?', (result_id,)).fetchone()

        if result is None:
            raise HTTPException(status_code=404, detail='Not found')

        conn.execute('DELETE FROM exam_results WHERE id = ?', (result_id,))

        return {'message': 'Result removed'}

@router.get('/report/{enrollment_id}')
def get_student_report(enrollment_id: int, current_user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        # ۱. اطلاعات ثبت‌نام
        enrollment = conn.execute('''
            SELECT
                student_enrollment.id,
                students.name AS student_name,
                students.father_name,
                students.grandfather_name,
                students.student_number,
                classes.class_name,
                academic_years.year AS academic_year
            FROM student_enrollment
            JOIN students ON student_enrollment.student_id = students.id
            JOIN classes ON student_enrollment.class_id = classes.id
            JOIN academic_years ON student_enrollment.academic_year_id = academic_years.id
            WHERE student_enrollment.id = ?
        ''', (enrollment_id,)).fetchone()

        if enrollment is None:
            raise HTTPException(status_code=404, detail='Enrollment not found')

        # ۲. نمرات به تفکیک مضمون
        subjects_data = conn.execute('''
            SELECT
                subjects.id AS subject_id,
                subjects.name AS subject_name,
                MAX(CASE WHEN exam_results.exam_type = 'midyear' THEN exam_results.score END) AS midyear_score,
                MAX(CASE WHEN exam_results.exam_type = 'annual' THEN exam_results.score END) AS annual_score,
                COALESCE(MAX(CASE WHEN exam_results.exam_type = 'midyear' THEN exam_results.score END), 0)
                + COALESCE(MAX(CASE WHEN exam_results.exam_type = 'annual' THEN exam_results.score END), 0) AS total_score
            FROM subjects
            LEFT JOIN exam_results
                ON exam_results.subject_id = subjects.id
                AND exam_results.enrollment_id = ?
            GROUP BY subjects.id
            ORDER BY subjects.name
        ''', (enrollment_id,)).fetchall()
        
        subjects_list = [dict(s) for s in subjects_data]
        
        # ۳. محاسبه معدل و وضعیت
        total_score = 0
        subjects_count = 0
        for s in subjects_list:
            if s['midyear_score'] is not None or s['annual_score'] is not None:
                total_score += s['total_score']
                subjects_count += 1
        
        average = round(total_score / subjects_count, 2) if subjects_count > 0 else 0
        status = 'قبول' if average >= 50 else 'رود'

        # ۴. محاسبه آمار حاضری
        attendance_stats = conn.execute('''
            SELECT status, COUNT(*) as count 
            FROM attendance 
            WHERE enrollment_id = ? 
            GROUP BY status
        ''', (enrollment_id,)).fetchall()
        
        att_dict = {row['status']: row['count'] for row in attendance_stats}
        
        present = att_dict.get('present', 0)
        absent = att_dict.get('absent', 0)
        excused = att_dict.get('excused', 0)
        sick = att_dict.get('sick', 0)
        
        total_absent = absent + excused + sick 

        return {
            'enrollment': dict(enrollment),
            'subjects': subjects_list,
            'summary': {
                'total_score': total_score,
                'average': average,
                'status': status
            },
            'attendance': {
                'present': present,
                'absent': total_absent,
                'total_days': present + total_absent,
                'total_hours': (present + total_absent) * 6
            }
        }
        
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import io

@router.get('/report/{enrollment_id}/excel')
def download_excel_report(enrollment_id: int, current_user: dict = Depends(get_current_user)):
    # ۱. گرفتن دیتا (دقیقاً مثل قبل)
    with get_connection() as conn:
        enrollment = conn.execute('''
            SELECT students.name, classes.class_name, academic_years.year
            FROM student_enrollment
            JOIN students ON student_enrollment.student_id = students.id
            JOIN classes ON student_enrollment.class_id = classes.id
            JOIN academic_years ON student_enrollment.academic_year_id = academic_years.id
            WHERE student_enrollment.id = ?
        ''', (enrollment_id,)).fetchone()
        
        if enrollment is None:
            raise HTTPException(status_code=404, detail='Enrollment not found')

        subjects_data = conn.execute('''
            SELECT subjects.name AS subject_name,
                MAX(CASE WHEN exam_results.exam_type = 'midyear' THEN exam_results.score END) AS midyear_score,
                MAX(CASE WHEN exam_results.exam_type = 'annual' THEN exam_results.score END) AS annual_score
            FROM subjects
            LEFT JOIN exam_results ON exam_results.subject_id = subjects.id AND exam_results.enrollment_id = ?
            GROUP BY subjects.id ORDER BY subjects.name
        ''', (enrollment_id,)).fetchall()

    # ۲. ساختن فایل اکسل با استایل
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "اطلاعنامه"
    ws.sheet_view.rightToLeft = True  # راست‌چین کردن شیت

    # استایل‌ها
    header_font = Font(bold=True, size=14)
    header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    header_text = Font(color="FFFFFF", bold=True, size=12)
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # عنوان
    ws.merge_cells('A1:D1')
    ws['A1'] = f"اطلاعنامه - {enrollment['name']} - صنف {enrollment['class_name']} - سال {enrollment['year']}"
    ws['A1'].font = header_font
    ws['A1'].alignment = center_align

    # هدر جدول
    headers = ['مضامین', 'نمره سالانه', 'نمره وسط سال', 'مجموع']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_text
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # داده‌ها
    row_num = 4
    total_sum = 0
    for sub in subjects_data:
        total = (sub['midyear_score'] or 0) + (sub['annual_score'] or 0)
        total_sum += total
        
        ws.cell(row=row_num, column=1, value=sub['subject_name']).border = thin_border
        ws.cell(row=row_num, column=2, value=sub['annual_score'] or '-').alignment = center_align
        ws.cell(row=row_num, column=2).border = thin_border
        ws.cell(row=row_num, column=3, value=sub['midyear_score'] or '-').alignment = center_align
        ws.cell(row=row_num, column=3).border = thin_border
        ws.cell(row=row_num, column=4, value=total if total > 0 else '-').alignment = center_align
        ws.cell(row=row_num, column=4).border = thin_border
        row_num += 1

    # ردیف مجموع
    ws.cell(row=row_num, column=1, value="مجموعه نمرات").font = Font(bold=True)
    ws.cell(row=row_num, column=4, value=total_sum).font = Font(bold=True)
    for col in range(1, 5):
        ws.cell(row=row_num, column=col).border = thin_border
        ws.cell(row=row_num, column=col).fill = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")

    # ۳. ذخیره در حافظه و ارسال به مرورگر
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    return StreamingResponse(
        stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{enrollment_id}.xlsx"}
    )