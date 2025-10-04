import os
import logging
import json
from pydantic import BaseModel,Field
from typing import List
from google import genai
from dotenv import load_dotenv
from app.core.config import settings
from pydantic import BaseModel, Field
import asyncio

load_dotenv()

GEMINI_API_KEY = settings.GEMINI_API_KEY


class AnalyzeRessume(BaseModel):
    match_score: int = Field(description="Overall match score between resume and job description (0-100)")
    matched_skills: List[str] = Field(description="List of skills present in both resume and job description")
    missing_skills: List[str] = Field(description="List of important skills from job description missing in resume")
    key_highlights: List[str] = Field(description="Relevant strengths and achievements from the resume")
    questions: List[str] = Field(description="Five interview questions based on the job description and resume")


class KeyMetrics(BaseModel):
    response_time: int = Field(description="Response time in seconds")
    filler_words: int = Field(description="Count of filler words")
    speech_rate: int = Field(description="Words per minute (wpm)")
    confidence_level: str = Field(description="Low, Medium, or High")

class AnalyzeAnswer(BaseModel):
    communication_score: int = Field(description="Communication score (0-100)")
    fluency: int = Field(description="Fluency score (0-100)")
    clarity: int = Field(description="Clarity score (0-100)")
    professionalism: int = Field(description="Professionalism score (0-100)")
    key_metrics: KeyMetrics
    feedback: List[str] = Field(description="Feedback on communication performance")

async def analyze_resume_with_gemini(job_description: str, resume_content: str):
    try:
        system_prompt = f"""
            You are an AI Resume-to-Job Matcher.  
            Your task is to analyze the provided job description and resume, and return a JSON object with the following fields:

            {{
            "match_score": <integer from 0–100 representing how well the resume matches the job description>,
            "matched_skills": [<list of skills explicitly found in both job description and resume>],
            "missing_skills": [<list of important skills from job description not found in resume>],
            "key_highlights": [<bullet points of notable strengths, achievements, or experiences from the resume most relevant to the job description>],
            "questions": [<list of 5 interview questions based on the job description and resume>]
            }}

            ### Input
            Job Description: {job_description}
            Resume Content: {resume_content}

            ### Output
            Return only the JSON object in the exact format described above, without additional commentary.
        """
        
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[AnalyzeRessume],
            },
            # config=types.GenerateContentConfig(
            #     thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            # ),
        )
        event = response.parsed
        data = [analyze.model_dump() for analyze in event]
        event_dict = data[0]
        return event_dict
    except:
        logging.exception("Exception occurred in analyze_resume_with_gemini")
        return None
    
async def analyze_answer_with_gemini(answer_obj:dict):
    try:
        system_prompt = """
            You are an AI evaluator that analyzes communication performance across multiple questions and answers.
            You must generate a **Communication Analysis** report with the following structure:

            1. **Communication Score**: A single number between 0–100 representing overall communication ability, based on fluency, clarity, and professionalism.
            2. **Fluency, Clarity, Professionalism**: Each must be a number between 0–100.

            * **Fluency** reflects smoothness and natural flow of speech.
            * **Clarity** reflects how well the message is conveyed.
            * **Professionalism** reflects tone, politeness, and structure.
            3. **Key Metrics**:

            * **Response Time**: Average time taken to answer each question, in seconds.
            * **Filler Words**: Count of filler words like "um," "uh," "like."
            * **Speech Rate**: Words per minute (wpm).
            * **Confidence Level**: Low, Medium, or High.
            4. **Feedback**: 3–5 bullet points summarizing strengths (or weaknesses if score is low). Each bullet must be concise and actionable.

            **Important Rules:**

            * Scores should be consistent with input performance.
            * If answers are detailed, clear, and confident, give high scores.
            * If answers are vague or hesitant, lower clarity or fluency.
            * Communication Score should be a weighted average: (Fluency 35%, Clarity 35%, Professionalism 30%).
            * Return results in JSON format with the following fields:

            {
            "communication_score": 72,
            "fluency": 93,
            "clarity": 92,
            "professionalism": 97,
            "key_metrics": {
                "response_time": "2.3s",
                "filler_words": 3,
                "speech_rate": "145 wpm",
                "confidence_level": "High"
            },
            "feedback": [
                "Clear and articulate communication",
                "Professional tone throughout",
                "Good use of examples and specifics",
                "Confident delivery"
            ]
            }
        """

        system_prompt += f"Input: {json.dumps(answer_obj)}"
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[AnalyzeAnswer],
            },
            # config=types.GenerateContentConfig(
            #     thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            # ),
        )
        event = response.parsed
        data = [analyze.model_dump() for analyze in event]
        event_dict = data[0]
        return event_dict
    
    except:
        logging.exception("Exception occurred in analyze_resume_with_gemini")
        return None
    
async def transcribe_audio(audio_file_path: str):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        audio_part = client.files.upload(file=audio_file_path)

        prompt = "Transcribe this audio clip."

        response = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=[prompt, audio_part]
        )
        return response.text
    except Exception as e:
        raise


async def generate_quiz_with_gemini(job_description: str, resume_content: str):
    try:
        system_prompt = f"""
            You are an AI Quiz Generator.
            Your task is to analyze the provided job description and resume, and return a JSON object with the following fields:

            {{
            "quiz": [
            {{
                "question": <question text>,
                "options": [<list of 4 options>],
                "correct_answer": <correct answer>
            }},
            ... (total 10 questions)
            ]
            }}

            ### Requirements
            - Generate exactly 10 quiz questions.
            - Each question must have 4 options and only 1 correct answer.
            - Questions should be relevant to the job description and resume content.

            ### Input
            Job Description: {job_description}
            Resume Content: {resume_content}

            ### Output
            Return only the JSON object in the exact format described above, without additional commentary.
        """
        
        class QuizQuestion(BaseModel):
            question: str = Field(description="Quiz question text")
            options: List[str] = Field(description="List of 4 options")
            correct_answer: str = Field(description="Correct answer for the question")

        class QuizResponse(BaseModel):
            quiz: List[QuizQuestion] = Field(description="List of quiz questions")

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config={
            "response_mime_type": "application/json",
            "response_schema": list[QuizResponse],
            },
        )
        event = response.parsed
        data = [quiz.model_dump() for quiz in event]
        event_dict = data[0]
        return event_dict
    except:
        logging.exception("Exception occurred in generate_quiz_with_gemini")
        return None



# create function that genrate qaution from job description and resume content 
# System Design , Code Review, Problem Solving,Database Design,Performance Optimization , for this i want only 5 quastion and ans , not options 

async def generate_interview_questions(job_description: str, resume_content: str):
    try:
        system_prompt = f"""
            You are an AI Interview Question & Answer Generator.
            Your task is to generate 5 interview questions and their answers based on the provided job description and resume content.

            ### Requirements
            - Generate exactly 5 interview questions.
            - For each question, provide a concise and relevant answer.
            - Questions should cover System Design, Code Review, Problem Solving, Database Design, and Performance Optimization.
            - Each question and answer should be relevant to the job description and resume content.

            ### Input
            Job Description: {job_description}
            Resume Content: {resume_content}

            ### Output
            Return only a JSON object in the following format, without additional commentary:
            {{
                "questions": [
                    {{
                        "question": "<question text>",
                        "answer": "<answer text>"
                    }},
                    ...
                    (total 5)
                ]
            }}
        """

        class InterviewQA(BaseModel):
            question: str = Field(description="Interview question text")
            answer: str = Field(description="Answer to the interview question")

        class InterviewQAResponse(BaseModel):
            questions: List[InterviewQA] = Field(description="List of interview questions and answers")

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[InterviewQAResponse],
            },
        )
        event = response.parsed
        data = [qa.model_dump() for qa in event]
        event_dict = data[0]
        return event_dict
    except Exception:
        logging.exception("Exception occurred in generate_interview_questions")
        return None
    
async def generate_interview_text_questions_questions(job_description: str, resume_content: str):
    try:
        system_prompt = f"""
            You are an **AI Interview Question & Answer Generator**. 
            Your role is to create **exactly 5 structured interview questions and answers** tailored to the given job description and candidate’s resume.

            ### Instructions
            - Generate **exactly 5** interview questions.
            - Each question must be **clear, specific, and relevant** to both the job description and the candidate’s resume.
            - Each answer must be **concise (2–4 sentences)**, professional, and aligned with the candidate’s skills and experience.
            - Focus on **technical expertise, problem-solving, past experience, and role-specific competencies**.
            - Do not include filler or generic questions (e.g., “Tell me about yourself”).
            - Strictly output in **valid JSON** matching the schema below.

            ### Input
            Job Description: {job_description}
            Resume Content: {resume_content}

            ### Output Format
            Return ONLY a JSON object in this exact structure, with no extra commentary:

            {{
            "questions": [
                {{
                "question": "string",
                "answer": "string"
                }},
                {{
                "question": "string",
                "answer": "string"
                }},
                {{
                "question": "string",
                "answer": "string"
                }},
                {{
                "question": "string",
                "answer": "string"
                }},
                {{
                "question": "string",
                "answer": "string"
                }}
            ]
            }}
        """

        class InterviewQA(BaseModel):
            question: str = Field(description="Interview question text")
            answer: str = Field(description="Answer to the interview question")

        class InterviewQAResponse(BaseModel):
            questions: List[InterviewQA] = Field(description="List of interview questions and answers")

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[InterviewQAResponse],
            },
        )
        event = response.parsed
        data = [qa.model_dump() for qa in event]
        event_dict = data[0]
        return event_dict
    except Exception:
        logging.exception("Exception occurred in generate_interview_questions")
        return None
    
# create function that take Qu and ans and retrun score from that 
# means for each qu and ans it will give score from 0 to 100
# fluency , clarity , professionalism
# in inpurt we give also qu Uid from that we have to chek original ans and user's ans and give score
# and also give overall score from 0 to 100
# it is for only one qu adn ans 

async def score_interview_answer(question: str, user_answer: str):
    """Scores a user's interview answer and returns a JSON object with overall_score."""
    try:
        system_prompt = f"""
        Your task is to evaluate the user's answer to the interview question and provide a single overall score.

        ### Requirements
        - Output only a JSON object with the following field:
        {{
            "overall_score": <float from 0.0-100.0 representing the overall quality of the user's answer>
        }}

        ### Evaluation Criteria
        - Relevance: How well the answer addresses the question.
        - Completeness: Whether the answer fully covers important aspects of the question.
        - Clarity: How clear, structured, and understandable the answer is.
        - Correctness: Whether the answer is factually accurate and appropriate.

        ### Input
        Question: {question}
        User's Answer: {user_answer}

        """

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {"overall_score": {"type": "number"}},
                    "required": ["overall_score"],
                },
            },
        )

        return response.parsed  # dict like {"overall_score": 85.3}

    except Exception:
        logging.exception("Exception occurred in score_interview_answer")
        return None
