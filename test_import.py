import time
print("Importing google.auth...")
t0 = time.time()
import google.auth
print("Done in", time.time() - t0)

print("Importing app.fast_api_app...")
t0 = time.time()
import app.fast_api_app
print("Done in", time.time() - t0)
