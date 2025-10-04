import os
from dotenv import load_dotenv

load_dotenv()

"""
This main file and we have to run this file and this application
runs on uvicorn server on 8003 port.
"""

if __name__ == "__main__":
    os.system("uvicorn app.main:app --reload --host 0.0.0.0 --port 7001")