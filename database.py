import sqlite3

DATABASE_NAME = 'database.db'

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn
    
def create_tables():
    with get_connection() as conn:

        conn.execute('''
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS teachers(
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL)
        ''')
        
        columns = [row['name'] for row in conn.execute('PRAGMA table_info (teachers)').fetchall()
        ]
        
        if 'is_active' not in columns:
            conn.execute('ALTER TABLE teachers ADD COLUMN is_active INTEGER DEFAULT 1')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS classes(
        id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        class_name TEXT NOT NULL,
        
        UNIQUE(student_id, teacher_id, class_name),
        
        FOREIGN KEY(student_id) REFERENCES students (id),
        
        FOREIGN KEY(teacher_id) REFERENCES teachers(id)
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS exam_results(
            id INTEGER PRIMARY KEY,
            enrollment_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            exam_type TEXT NOT NULL
                CHECK(exam_type IN ('midyear', 'annual')),
            score INTEGER NOT NULL,
            CHECK(
                (exam_type = 'midyear' AND score BETWEEN 0 AND 40)
                OR
                (exam_type = 'annual' AND score BETWEEN 0 AND 60)
            ),
            UNIQUE(enrollment_id, subject_id, exam_type),
            FOREIGN KEY(enrollment_id)
                REFERENCES student_enrollment(id),
            FOREIGN KEY(subject_id)
                REFERENCES subjects(id)
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS academic_years(id INTEGER PRIMARY KEY, year INTEGER NOT NULL UNIQUE)
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS student_enrollment(
            id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            academic_year_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            enrollment_date TEXT,
            exit_date TEXT,
            
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(academic_year_id) REFERENCES academic_years(id),
            FOREIGN KEY(class_id) REFERENCES classes(id)
)
''')

        conn.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS unique_active_enrollment
        ON student_enrollment(student_id, academic_year_id)
        WHERE exit_date IS NULL
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS student_login(id INTEGER PRIMARY KEY,
        student_id INTEGER UNIQUE NOT NULL, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        FOREIGN KEY(student_id)REFERENCES students(id)
        )
        ''')
        
        existing_admin = conn.execute("SELECT id FROM admins WHERE username = 'admin'").fetchone()
        
        if not existing_admin:
            conn.execute("INSERT INTO admins(username, password) VALUES(?,?)"
            ,('admin', '1234')
            )
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS teacher_subjects(
            id INTEGER PRIMARY KEY,
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            UNIQUE(teacher_id, subject_id, class_id),
            FOREIGN KEY(teacher_id) REFERENCES teachers(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id),
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS teacher_logins(
            id INTEGER PRIMARY KEY,
            teacher_id INTEGER UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id)
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY, enrollment_id INTEGER NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('present', 'absent', 'late', 'excused')), UNIQUE (enrollment_id, date),
        FOREIGN KEY(enrollment_id)REFERENCES student_enrollment(id)
        )
        ''')
        
        # اضافه کردن ستون عکس به جدول‌ها
# برای دانش‌آموزان
        cols = [r['name'] for r in conn.execute('PRAGMA table_info(students)').fetchall()]
        if 'profile_picture' not in cols:
            conn.execute('ALTER TABLE students ADD COLUMN profile_picture TEXT')
        
        # برای معلمان
        cols = [r['name'] for r in conn.execute('PRAGMA table_info(teachers)').fetchall()]
        if 'profile_picture' not in cols:
            conn.execute('ALTER TABLE teachers ADD COLUMN profile_picture TEXT')
        
        # برای مدیران
        cols = [r['name'] for r in conn.execute('PRAGMA table_info(admins)').fetchall()]
        if 'profile_picture' not in cols:
            conn.execute('ALTER TABLE admins ADD COLUMN profile_picture TEXT')