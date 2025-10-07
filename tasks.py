from celery_app import celery_app
import asyncio
import sys
from datetime import datetime
from collections import defaultdict
from datetime import timedelta
from app.utils.common import process_quiz_questions

@celery_app.task(name="tasks.process_job_task")
def process_job_task(candidate_id_str,job_description,extracted_text):
    print(f"Starting process_job_task")
    sys.stdout.flush()
    
    async def _process_job_task(candidate_id_str,job_description,extracted_text):
        try:
            process_quiz_questions(candidate_id_str,job_description,extracted_text)
        except Exception as e:
            # Best-effort background job; failures are not propagated to the client
            print(f"Error in _process_job: {str(e)}")
            sys.stdout.flush()
            pass

    # Run async code in separate event loop
    asyncio.run(
        _process_job_task(
            candidate_id_str,job_description,extracted_text
        )
    )
