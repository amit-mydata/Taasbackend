import uuid
import asyncio
from app.utils.llm import generate_quiz_with_gemini, generate_interview_questions, generate_interview_text_questions_questions
from app.services.analyzer import AnalyzerService
analyzer_service = AnalyzerService()

async def process_quiz_questions(candidate_id: str, job_description: str, extracted_text: str):
    """
    Runs in background: generate quiz questions and save to DB (or log).
    """
    try:
        print("Generating Quiz Questions...")
        quiz_response, interview_questions, text_questions = await asyncio.gather(
            generate_quiz_with_gemini(job_description, extracted_text),
            generate_interview_questions(job_description, extracted_text),
            generate_interview_text_questions_questions(job_description, extracted_text)
        )

        print("Generated Quiz Response:", quiz_response)  
        print("Generated Interview Questions:", interview_questions)  
        print("Generated Interview Text Questions:", text_questions)

        quiz_list = []
        # Collect all quiz items
        if candidate_id and quiz_response and "quiz" in quiz_response:
            quiz_list = []
            for quiz_item in quiz_response["quiz"]:
                if isinstance(quiz_item, dict):
                    quiz_data = {
                        "quiz_id": str(uuid.uuid4()),
                        "question": quiz_item.get("question", quiz_item),
                        "options": quiz_item.get("options", []),
                        "correct_answer": quiz_item.get("correct_answer", None),
                        "type": "mcqs_questions"
                    }
                quiz_list.append(quiz_data)

        
        # Add interview questions to quiz_list (with answer field)
        if candidate_id and interview_questions and "questions" in interview_questions:
            for qa in interview_questions["questions"]:
                quiz_data = {
                    "quiz_id": str(uuid.uuid4()),
                    "question": qa.get("question", ""),
                    "correct_answer": qa.get("answer", None), 
                    "type": "coding_questions"              
                }
                quiz_list.append(quiz_data)

        if candidate_id and text_questions and "questions" in text_questions:
            for qa in text_questions["questions"]:
                quiz_data = {
                    "quiz_id": str(uuid.uuid4()),
                    "question": qa.get("question", ""),
                    "correct_answer": qa.get("answer", None),
                    "type": "text_questions"
                }
                quiz_list.append(quiz_data)

        # Store once in DB
        await analyzer_service.store_quiz_questions(candidate_id, quiz_list)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in background quiz generation: {str(e)}")
        raise


async def calculate_overall_score(resume, communication, technical):

    weight_resume=40
    # weight_comm=20
    weight_tech=60

    if resume is None:
        resume = 0
    if communication is None:
        communication = 0
    if technical is None:
        technical = 0
    
    # total_weight = weight_resume + weight_comm + weight_tech
    total_weight = weight_resume + weight_tech
    score = (
        (resume * weight_resume) +
        # (communication * weight_comm) +
        (technical * weight_tech)
    ) / total_weight
    score = round(score, 2)

    # Category mapping for fit status
    if score >= 85:
        status = "Strong Fit"
    elif score >= 70:
        status = "Potential Fit"
    else:
        status = "Not a Fit"
    return score, status