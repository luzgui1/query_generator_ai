import os

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable is not set")
else:
    print(os.environ.get("GOOGLE_API_KEY"))