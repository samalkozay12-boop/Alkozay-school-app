import uvicorn
import threading
import webbrowser

def open_browser():
    # به جای docs، مستقیماً فایل HTML خودمان را باز می‌کند
    webbrowser.open('file:///storage/emulated/0/School management/index.html')

if __name__ == "__main__":
    print("در حال روشن کردن سرور...")
    print("صبر کن، صفحه وب باز می‌شود...")
    threading.Timer(2.0, open_browser).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000)