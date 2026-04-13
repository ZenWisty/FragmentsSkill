# Diagnostic entry point - replaces __main__.py temporarily
import sys
import os
import traceback

LOG_PATH = '/data/data/com.obsidian.task.reviewhelperapp/files/app.log'
ANDROID_FILES = '/data/data/com.obsidian.task.reviewhelperapp/files'
SRC_PATH = os.path.join(ANDROID_FILES, 'src')

def log(msg):
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(msg + '\n')
    except:
        pass
    print(msg)

try:
    log("=== APK Diagnostic ===")
    log(f"Python: {sys.version}")
    log(f"Executable: {sys.executable}")
    log(f"CWD: {os.getcwd()}")
    log(f"ARGV: {sys.argv}")

    # List files in android files dir
    try:
        files = os.listdir(ANDROID_FILES)
        log(f"Files in {ANDROID_FILES}: {files[:10]}")
    except Exception as e:
        log(f"Cannot list {ANDROID_FILES}: {e}")

    # Try src path
    try:
        if os.path.exists(SRC_PATH):
            log(f"src exists: {os.listdir(SRC_PATH)}")
            src_files = os.listdir(SRC_PATH)
            log(f"src contents: {src_files}")
        else:
            log(f"SRC_PATH not found: {SRC_PATH}")
    except Exception as e:
        log(f"Cannot list src: {e}")

    # Add to path
    sys.path.insert(0, SRC_PATH)
    log(f"sys.path[0]: {sys.path[0]}")

    # Test import
    log("Testing import...")
    import reviewhelperapp.communication
    log("reviewhelperapp.communication OK")

    import reviewhelperapp.app
    log("reviewhelperapp.app OK")

    log("All imports successful, starting main app...")
    from reviewhelperapp.app import main
    main()

except Exception as e:
    log(f"FATAL ERROR: {e}")
    log(traceback.format_exc())
