from fastapi import FastAPI, status, BackgroundTasks
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from tasks import process_job_task
from app.utils.common import process_quiz_questions
import os
app = FastAPI()
# Define a Pydantic model for the request body
class BackgroundProcessRequest(BaseModel):
    candidate_id: str
    job_description: str
    extracted_text: str

# POST route
@app.post("/background-process/")
async def background_job(data: BackgroundProcessRequest, background_tasks: BackgroundTasks):
    try:
        print("??????????/Request Received")
        candidate_id = data.candidate_id
        job_description = data.job_description
        extracted_text = data.extracted_text
        print(f"candidate_id: {candidate_id}")
        print(f"job_description: {job_description}")    
        print(f"extracted_text: {extracted_text}")
        process_job_task.delay(
            candidate_id,
            job_description,
            extracted_text
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": False,
                "message": "Something went wrong"
            }
        )
# To run: uvicorn main:app --reload
if __name__ == "__main__":
    os.system("uvicorn background_task:app --reload --host 0.0.0.0 --port 7002")