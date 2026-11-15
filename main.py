from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from database import create_tables
from routers.students import router as students_router
from routers.subjects import router as subjects_router
from routers.teachers import router as teachers_router
from routers.classes import router as classes_router
from routers.results import router as result_router
from routers.academic_years import router as academic_years_router
from routers.enrollment import router as enrollment_router
from routers.dashbord import router as dashboard_router
from routers.attendance import router as attendance_router
from routers.auth import router as auth_router
from routers.teacher_subjects import router as teacher_subject_router
from routers.upload import router as upload_router

app = FastAPI()

# فعال‌سازی CORS برای اینکه مرورگر با API حرف بزنه
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

# اتصال روترها
app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(subjects_router)
app.include_router(classes_router)
app.include_router(result_router)
app.include_router(academic_years_router)
app.include_router(enrollment_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(teacher_subject_router)
app.include_router(attendance_router)
app.include_router(upload_router)

# مسیر اصلی پوشه
BASE_DIR = "/storage/emulated/0/School management"

# آدرس‌های صفحات HTML
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/students-page")
def students_page():
    return FileResponse(os.path.join(BASE_DIR, "students.html"))
    
@app.get("/teachers-page")
def teachers_page():
    return FileResponse(os.path.join(BASE_DIR, "teachers.html"))
    
@app.get("/classes-page")
def classes_page():
    return FileResponse(os.path.join(BASE_DIR, "classes.html"))

@app.get("/subjects-page")
def subjects_page():
    return FileResponse(os.path.join(BASE_DIR, "subjects.html"))
    
@app.get("/enrollments-page")
def enrollments_page():
    return FileResponse(os.path.join(BASE_DIR, "enrollments.html"))
    
@app.get("/results-page")
def results_page():
    return FileResponse(os.path.join(BASE_DIR, "results.html"))
    
@app.get("/student-panel")
def student_panel():
    return FileResponse(os.path.join(BASE_DIR, "student-panel.html"))
    
@app.get("/login-page")
def login_page():
    return FileResponse(os.path.join(BASE_DIR, "login.html"))
    
@app.get("/login")
def login_page():
    return FileResponse(os.path.join(BASE_DIR, "login.html"))
    
@app.get("/teacher-assignments")
def serve_teacher_assignments():
    return FileResponse(os.path.join(BASE_DIR, "teacher-assignments.html"))
    
@app.get("/report-card")
def report_card_page():
    return FileResponse(os.path.join(BASE_DIR, "report-card.html"))
    
@app.get("/attendance-page")
def attendance_page():
    return FileResponse(os.path.join(BASE_DIR, "attendance.html"))
    
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")