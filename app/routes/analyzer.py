from fastapi import APIRouter,Depends, File, Form, UploadFile, Request, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from typing import List
import os
import tempfile
import fitz  
import uuid
import asyncio
from app.utils.llm import analyze_resume_with_gemini, transcribe_audio, score_interview_answer, analyze_answer_with_gemini
from app.models.analyzer import SingleQuizQuestion
from app.utils.common import calculate_overall_score , extract_text_and_tables, convert_objectids
from app.services.analyzer import AnalyzerService
from tasks import process_job_task
from app.utils.auth import get_current_user
from fastapi.encoders import jsonable_encoder


analyze_router = APIRouter()
analyzer_service = AnalyzerService()


@analyze_router.post("/upload")
async def upload(
    request: Request,
    candidate_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    hr_name: str = Form(...),
    job_position: str = Form(...),    
    job_description: str = Form(...),
    resume: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    try:
        candidate_data = await analyzer_service.get_candidate_by_email(email)
        user_id = str(current_user["_id"])

        # if candidate_data:
        #     return JSONResponse(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         content={"status": False, "message": "Candidate with this email already exists."}
        #     )
        candidate_id = await analyzer_service.add_candidate_info({
            "candidate_name": candidate_name,
            "user_id": user_id,
            "email": email,
            "phone": phone,
            "hr_name": hr_name,
            "job_position": job_position
        })

        # suffix = os.path.splitext(resume.filename)[-1].lower()
        # with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        #     temp_file_path = tmp.name
        #     content = await resume.read()
        #     tmp.write(content)

        extracted_text = ""

        # # Process based on file type
        # if suffix == ".pdf":
        #     doc = fitz.open(temp_file_path)
        #     extracted_text = "".join(page.get_text("text") for page in doc)
        #     doc.close()

        # elif suffix == ".docx":
        #     extracted_text = extract_text_and_tables(temp_file_path)

        # else:
        #     os.remove(temp_file_path)
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Only PDF and DOCX resumes are supported right now."
        #     )

        # # Cleanup temp file
        # os.remove(temp_file_path)

        # response = await analyze_resume_with_gemini(job_description,extracted_text)

        # await analyzer_service.add_analyzed_data({
        #     "candidate_id": candidate_id,
        #     "user_id": user_id,
        #     "resume_text": extracted_text,
        #     "job_description": job_description,
        #     "analyze_answer_response": response,
        # })

        candidate_id_str = str(candidate_id)
        process_job_task.delay(
            candidate_id_str,
            job_description,
            extracted_text
        )


        # result = {
        #     "candidate_id": candidate_id_str,
        #     "user_id": user_id,
        #     "candidate_name": candidate_name,
        #     "email": email,
        #     "phone": phone,
        #     "hr_name": hr_name,
        #     "job_position": job_position,
        #     "job_description": job_description,
        #     "analysis": response, 
        # }

        result = {
        "candidate_id": "68e6470c392eb9b2b3895ef4",
        "user_id": "68e63751183642e3eff9fb96",
        "candidate_name": "assssavvaa",
        "email": "sssdaecfvfv@gmail.com",
        "phone": "1212121212",
        "hr_name": "meet",
        "job_position": "developer",
        "job_description": "data science",
        "analysis": {
            "match_score": 20,
            "matched_skills": [
                "Data Analysis",
                "Data Visualization",
                "Reporting",
                "Power BI",
                "Advanced Excel",
                "Cognos"
            ],
            "missing_skills": [
                "Machine Learning",
                "Statistical Modeling",
                "Python",
                "R",
                "SQL",
                "Predictive Analytics",
                "Big Data Technologies"
            ],
            "key_highlights": [
                "Over 11 years of experience incorporating data analysis, data visualization, and BI reporting within the IT Asset Management domain.",
                "Proficient with data analytics and BI tools such as Power BI, Advanced Excel, and Cognos.",
                "Extensive experience in creating and managing KPI reports, dashboards (in Excel and ServiceNow), and conducting data reconciliation and gap analysis.",
                "Developed a Hardware Asset Finance Portfolio Dashboard using Advanced Excel."
            ],
            "questions": [
                "Your resume highlights strong data analysis and reporting skills within IT Asset Management. Can you describe how you would transition these skills to a broader data science context that might involve predictive modeling?",
                "Can you provide an example of a complex business problem you solved using data analysis, and walk me through the steps you took, from data gathering to presenting your conclusions?",
                "This role requires proficiency in tools commonly used in data science, such as Python or R. What is your experience with these programming languages and their data science libraries?",
                "Describe a time you used data visualization to reveal an insight that was not obvious from the raw data. What tools did you use, and what was the impact of your discovery?",
                "How do you ensure data quality and integrity in your analysis and reporting, particularly when dealing with data from multiple sources like SCCM, BigFix, or ServiceNow?"
            ]
        }
    },

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": True,
                "data": result,
                "message": "Resume analyzed successfully"
            }
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
    
@analyze_router.post("/submit-all-answers")
async def submit_all_answers(
    request: Request,
    candidate_id: str = Form(...),
    question_texts: List[str] = Form(...), 
    recordings: List[UploadFile] = None,
    current_user=Depends(get_current_user)
):
    try:
        user_id = str(current_user["_id"])

        answers_batch = []
        temp_folder = "temp_audio"
        os.makedirs(temp_folder, exist_ok=True)
        for question,recording in zip(question_texts,recordings):
            audio_content = await recording.read()
            filename = f"{uuid.uuid4()}.mp3" 
            filepath = os.path.join(temp_folder, filename)
            with open(filepath, "wb") as f:
                f.write(audio_content)
            transcription = await transcribe_audio(filepath)
            os.remove(filepath)
            que_obj = {
                "questions": question,
                "answers": transcription
            }
            answers_batch.append(que_obj)

        data = await analyze_answer_with_gemini(answers_batch)

        await analyzer_service.add_communication_data(
            candidate_id = candidate_id,
            communication_data = data
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": True,
                "user_id": user_id,
                "data": data,
                "message": "Answers analyzed successfully"
            }
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

@analyze_router.post("/submit-single-answer")
async def submit_single_answer(
    request: Request,
    data: SingleQuizQuestion = Body(...),
    current_user=Depends(get_current_user)
):
    try:
        candidate_uid = data.candidate_uid
        quiz_id = data.quiz_id
        user_id = str(current_user["_id"])
        user_answer = data.user_answer
        question_type = data.type

        quiz_data = await analyzer_service.get_quiz_question_by_id(candidate_uid, quiz_id)
        if not quiz_data:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": False,
                    "message": "Quiz question not found"
                }
            )
        question = quiz_data.get("question", "")
        original_answer = quiz_data.get("correct_answer", "")

        if question_type == "coding_questions" or question_type == "text_questions":
            res = await score_interview_answer(question, user_answer)
            overall_score = res["overall_score"]

        else:
            if user_answer == original_answer:
                overall_score = 100
            else:
                overall_score = 0


        await analyzer_service.save_score(candidate_id=candidate_uid, quiz_id=quiz_id, score_type=question_type, score=overall_score)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": True,
                "user_id": user_id,
                # "data": data,
                "message": "Answer analyzed successfully"
            }
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
    
@analyze_router.get("/get-quiz-questions")
async def get_quiz_questions(request: Request, candidate_uid: str = Query(...),current_user=Depends(get_current_user)):
    try:
        data = await analyzer_service.get_quiz_questions(candidate_uid)
        user_id = str(current_user["_id"])
        count = 0
        if count > 5:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": False,
                    "message": "No questions found"
                }
            )
        while True:
            if data:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "status": True,
                        "user_id": user_id,
                        "data": data,
                        "message": "Questions fetched successfully"
                    }
                )
            else:
                data = await analyzer_service.get_quiz_questions(candidate_uid)
                count += 1
                await asyncio.sleep(10)
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": False,
                "message": "Something went wrong"
            }
        )

@analyze_router.get("/get-technical-data")
async def get_technical_data(request: Request, candidate_uid: str = Query(...),current_user=Depends(get_current_user)):
    try:

        candidate_analysis = await analyzer_service.get_candidate_analysis_by_id(candidate_uid)  
        user_id = str(current_user["_id"])
        candidate_data = await analyzer_service.get_candidate_by_id(candidate_uid)
        # print(candidate_analysis)
        analyze_answer_response = candidate_analysis.get("analyze_answer_response")
        communication_data = candidate_analysis.get("communication_data")
    
        if not candidate_analysis:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": False,
                    "message": "Something went wrong"
                }
            )
    
        data = await analyzer_service.get_score(candidate_uid)
        if not data:
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": False,
                    "message": "Something went wrong"
                }
            )
        
        mcq_scores = []
        coding_scores = []
        text_scores = []

        # Loop through and categorize
        for item in data:
            if item.get("type") == "mcqs_questions":
                mcq_scores.append(item.get("score", 1))
            elif item.get("type") == "coding_questions":
                coding_scores.append(item.get("score", 1))
            elif item.get("type") == "text_questions":
                text_scores.append(item.get("score", 1))


        mcq_percentage = sum(mcq_scores) / len(mcq_scores)
        print(f"Experience-Based Score: {mcq_percentage}%")

        Experience_Based = mcq_percentage
        coding_percentage = sum(coding_scores) / len(coding_scores)
        text_percentage = sum(text_scores) / len(text_scores)

        overall_score = (mcq_percentage + coding_percentage + text_percentage) / 3

        # Store the technical score (overall_score) in MongoDB for this candidate
        try:
            # The store_analyzed_data_with_candidate_id expects a dict, not a float.
            technical_data_to_store = {
                "overall_score": overall_score,
                "experience_based": Experience_Based,
                "coding_percentage": coding_percentage,
                "text_percentage": text_percentage
            }
            await analyzer_service.store_analyzed_data_with_candidate_id(candidate_uid, technical_data_to_store)
        except Exception as e:
            print(f"Failed to store technical score for candidate {candidate_uid}: {e}")


        teachnical_data = {
            "experience_based": Experience_Based,
            "coding_percentage": coding_percentage,
            "text_percentage": text_percentage,
            "overall_score": overall_score
        }



        resume_score = analyze_answer_response.get("match_score")
        communication_score = analyze_answer_response.get("communication_score")
        main_score, fit  = await calculate_overall_score(resume=resume_score, communication=communication_score, technical=overall_score)

        final_data = {
            "candidate_data": candidate_data,
            "analyze_answer_response": analyze_answer_response,
            "communication_data": communication_data,
            "teachnical_data": teachnical_data,
            "main_score": main_score,
            "fit": fit
        }

         # Store the technical score (overall_score) in MongoDB for this candidate
        try:
            # The store_analyzed_data_with_candidate_id expects a dict, not a float.
            technical_data_to_store = {
                "technical_score": overall_score,
                "overall_score": main_score,
                "fit": fit
            }
            await analyzer_service.store_analyzed_data_with_candidate_id(candidate_uid, technical_data_to_store)
        except Exception as e:
            print(f"Failed to store technical score for candidate {candidate_uid}: {e}")
        
        print(final_data)
        safe_data = jsonable_encoder(convert_objectids(final_data))


        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": True,
                "user_id": str(current_user["_id"]),         
                "data": safe_data,
                "message": " Questions fetched successfully"
            }
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

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


# @analyze_router.get("/dashboard")
# async def get_dashboard():
#     try:
#         try:
#             # Fetch all assessments from MongoDB
#             assessments = await analyzer_service.get_all_assessments()

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return JSONResponse(
#                 status_code=status.HTTP_200_OK,
#                 content=jsonable_encoder({
#                     "status": True,
#                     "data": {"recent_assessments": []},
#                     "message": "No assessments found"
#                 })
#             )

#         if not assessments or len(assessments) == 0:
#             return JSONResponse(
#                 status_code=status.HTTP_200_OK,
#                 content=jsonable_encoder({
#                     "status": True,
#                     "data": {"recent_assessments": []},
#                     "message": "No assessments found"
#                 })
#             )

#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content=jsonable_encoder({
#                 "status": True,
#                 "data": {"recent_assessments": assessments},
#                 "message": "Dashboard data fetched successfully"
#             })
#         )

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content=jsonable_encoder({
#                 "status": False,
#                 "message": "Something went wrong"
#             })
#         )
    
@analyze_router.get("/dashboard")
async def get_dashboard(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100), search: str = Query(None), current_user=Depends(get_current_user)):
    try:
        skip_count = (page - 1) * per_page
        user_id = str(current_user["_id"])

        # Fetch paginated assessments
        assessments, total_count = await analyzer_service.get_all_assessments(skip=skip_count, limit=per_page, search=search, user_id=user_id)

        if not assessments:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=jsonable_encoder({
                    "status": True,
                    "data": {
                        "user_id": user_id,
                        "recent_assessments": [],
                        "page": page,
                        "per_page": per_page,
                        "total_pages": 0,
                        "total_count": 0
                    },
                    "message": "No assessments found"
                })
            )

        total_pages = (total_count + per_page - 1) // per_page

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder({
                "status": True,
                "data": {
                    "user_id": user_id,
                    "recent_assessments": assessments,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "total_count": total_count
                },
                "message": "Dashboard data fetched successfully"
            })
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder({
                "status": False,
                "message": "Something went wrong"
            })
        )


