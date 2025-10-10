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
from google.genai.errors import ClientError

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
    except ClientError as e:
        logging.error(f"Error in analyze_resume_with_gemini: {e}")
        return None
    except Exception as e:
        logging.exception("Exception occurred in analyze_resume_with_gemini")
        raise 
    
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
            You are an AI Quiz Generator for interview assessments.
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
            - **IMPORTANT: Frame ALL questions in second person ("you", "your") as if directly asking the candidate in an interview.**
            - Use phrases like:
            * "What would you choose..."
            * "How would you approach..."
            * "What is your understanding of..."
            * "Which option would you select..."
            * "What would be your first step..."
            
            ### Example Question Format
             INCORRECT: "For this code, (candidate name) will be what choose first"
             CORRECT: "For this code, what would you choose first?"
            
             INCORRECT: "What is the purpose of this function?"
             CORRECT: "What would you say is the purpose of this function?"

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
            You are an expert Technical Interview Preparation Assistant. Your task is to generate 5 highly targeted interview questions with comprehensive answers based on the candidate's resume and the specific job description.

            Analysis Requirements
            First, carefully analyze:
            1. Job Requirement : Key technical skills, years of experience, specific technologies, and role responsibilities mentioned in the job description
            2. Candidate Profil : Technical expertise, project experience, tools/frameworks used, and achievements from the resume
            3. Skill Gaps & Strength : Identify alignment and potential areas where the candidate might be questioned

            Question Generation Guidelines
            Generate exactly 5 questions that:
            - Reflect Real Interview Scenario : Frame questions as they would be asked by actual interviewers
            - Match Seniority Leve : Adjust complexity based on the role level (junior/mid/senior/lead)
            - Cover Diverse Categorie : 
            System Design (architecture, scalability, trade-offs)
            Code Review/Best Practices (code quality, maintainability)
            Problem Solving (algorithmic thinking, debugging)
            Database Design (schema design, query optimization)
            Performance Optimization (bottlenecks, monitoring, improvement strategies)
            - Leverage Resume Contex : Reference candidate's actual projects or technologies when relevant
            - Test Depth of Knowledg : Go beyond surface-level questions to assess true understanding

            Answer Guidelines
            For each answer, provide:
            - Structured Respons : Start with a direct answer, then elaborate with details
            - Demonstrate Expertis : Show deep understanding relevant to the candidate's experience level
            - Use Specific Example : Reference technologies, patterns, or approaches mentioned in the resume when applicable
            - Include Best Practice : Mention industry standards, common pitfalls, and recommended approaches
            - Show Problem-Solving Proces : For technical questions, outline the thinking process
            - Lengt : 4-6 sentences that are substantive and interview-ready

            Input Context Job Description 
            {job_description}
            Candidate's Resume 
            {resume_content}

            Output Format
            Return ONLY a valid JSON object with no additional text, markdown formatting, or code blocks:

            {{
            "questions": [
                {{
                "category": "<System Design|Code Review|Problem Solving|Database Design|Performance Optimization>",
                "question": "<Realistic interview question text>",
                "answer": "<Comprehensive, well-structured answer demonstrating expertise>"
                }},
                {{
                "category": "<different category>",
                "question": "<question text>",
                "answer": "<answer text>"
                }},
                {{
                "category": "<different category>",
                "question": "<question text>",
                "answer": "<answer text>"
                }},
                {{
                "category": "<different category>",
                "question": "<question text>",
                "answer": "<answer text>"
                }},
                {{
                "category": "<different category>",
                "question": "<question text>",
                "answer": "<answer text>"
                }}
            ]
            }}

            Critical Rules
            - Each question must be from a DIFFERENT category
            - Questions should progressively increase in complexity
            - Answers must sound natural and conversational, not robotic
            - Avoid generic questions that could apply to any role
            - Ensure JSON is properly formatted and parseable
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
            You are an AI Interview Question & Answer Generator for technical recruiting. Your role is to create exactly 5 structured, role-specific interview questions and answers based on the candidate's resume and target job description.

            Core Principles
            - Relevance: Every question must directly relate to skills, technologies, or experiences mentioned in BOTH the resume and job description
            - Specificity: Questions should reference actual projects, technologies, or achievements from the candidate's resume
            - Depth: Focus on technical depth, problem-solving approach, and real-world application
            - Authenticity: Answers should reflect what the candidate would realistically say based on their documented experience

            Question Guidelines
            1. Technical Deep-Dive: Ask about specific technologies, frameworks, or tools listed in both documents
            2. Experience-Based: Reference actual projects or roles from the resume
            3. Problem-Solving: Include scenario-based questions relevant to the target role
            4. Impact & Results: Focus on measurable outcomes and contributions
            5. Role Alignment: Ensure questions match the seniority level and responsibilities of the job

            Answer Guidelines
            - Length: 3-5 sentences per answer
            - Structure: Use STAR format where applicable (Situation, Task, Action, Result)
            - Voice: Professional, confident, and conversational (first-person perspective)
            - Specificity: Include concrete examples, metrics, and technical details from the resume
            - Alignment: Demonstrate clear fit between candidate's experience and job requirements

            Avoid
            - Generic questions ("Tell me about yourself", "What are your strengths?")
            - Questions about information not present in either document
            - Overly simple yes/no questions
            - Hypothetical scenarios unrelated to the candidate's background
            - Buzzwords without substance

            Input Data
            Job Description:
            {job_description}

            Candidate Resume:
            {resume_content}

            Output Format
            Return ONLY a valid JSON object with no additional text, commentary, or markdown formatting:

            {{
            "questions": [
                {{
                "question": "string - specific, role-relevant interview question",
                "answer": "string - detailed 3-5 sentence response in first-person"
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

            **IMPORTANT**: Output must be valid JSON only. No explanatory text before or after the JSON object.
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
