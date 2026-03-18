import time
print("Importing app.main...")
start = time.time()
try:
    from app.main import app
    print(f"Imported app.main in {time.time() - start:.2f}s")
except Exception as e:
    print(f"Error importing app.main: {e}")

print("Checking health endpoint...")
# This won't work easily without a test client, but we can check if it even gets here.
