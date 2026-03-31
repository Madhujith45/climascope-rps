import sys
import traceback

sys.path.append('.')
try:
    from app.main import app
    print("Successfully imported app")
except Exception as e:
    with open('err.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print("Error importing app, details written to err.txt")
