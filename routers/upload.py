from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil
import os
import uuid

import sys
sys.path.insert(0, '/storage/emulated/0/School management')
from database import get_connection
from routers.auth import get_current_user

router = APIRouter(prefix='/upload', tags=['Upload'])

# مسیر ذخیره عکس‌ها
UPLOAD_DIR = 'uploads'
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post('/profile-picture')
def upload_profile_picture(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    # چک کردن فرمت فایل
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="فرمت عکس باید JPG یا PNG باشد")

    # ساختن یه اسم یکتا برای فایل
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # ذخیره فایل
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ذخیره مسیر تو دیتابیس
    role = current_user.get('role')
    user_id = current_user.get('sub')

    with get_connection() as conn:
        if role == 'admin':
            conn.execute("UPDATE admins SET profile_picture = ? WHERE username = ?", (unique_filename, user_id))
        elif role == 'teacher':
            conn.execute("UPDATE teachers SET profile_picture = ? WHERE id = ?", (unique_filename, user_id))
        elif role == 'student':
            conn.execute("UPDATE students SET profile_picture = ? WHERE id = ?", (unique_filename, user_id))

    return {"message": "عکس با موفقیت آپلود شد", "filename": unique_filename}
    
from database import create_tables

@router.get('/fix-db')
def fix_database():
    create_tables()
    return {"message": "Database tables created/updated successfully!"}