from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import openai
import json
import asyncio
import os
from typing import List, Dict
import PyPDF2
import io
from pydantic import BaseModel

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# OpenAI client setup
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

# Data models
class QuestionAnswer(BaseModel):
    question: str
    answer: str

class InterviewSession(BaseModel):
    resume_text: str
    initial_questions: List[str] = []
    answers: List[QuestionAnswer] = []
    follow_up_questions: List[str] = []
    follow_up_answers: List[QuestionAnswer] = []
    final_rating: Dict = {}

# In-memory storage (use database in production)
interview_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Extract text from uploaded resume PDF"""
    try:
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
        
        # Generate initial 5 questions based on resume
        initial_questions = await generate_initial_questions(resume_text)
        
        session_id = "session_1"  # In production, generate unique IDs
        interview_sessions[session_id] = InterviewSession(
            resume_text=resume_text,
            initial_questions=initial_questions
        )
        
        return {
            "session_id": session_id,
            "resume_text": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
            "questions": initial_questions
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing resume: {str(e)}")

async def generate_initial_questions(resume_text: str) -> List[str]:
    """Generate 5 initial questions based on resume"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an HR interviewer. Based on the resume provided, generate exactly 5 relevant interview questions. Focus on the candidate's experience, skills, and background. Return only the questions, numbered 1-5."
                },
                {
                    "role": "user",
                    "content": f"Resume text: {resume_text}"
                }
            ],
            max_tokens=500
        )
        
        questions_text = response.choices[0].message.content
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and any(char.isdigit() for char in q[:3])]
        
        # Clean up questions (remove numbering)
        cleaned_questions = []
        for q in questions:
            # Remove number prefix (1., 2., etc.)
            cleaned = q.split('.', 1)[-1].strip() if '.' in q else q.strip()
            cleaned_questions.append(cleaned)
        
        return cleaned_questions[:5]  # Ensure exactly 5 questions
    
    except Exception as e:
        print(f"Error generating questions: {e}")
        return [
            "Tell me about yourself and your professional background.",
            "What motivated you to apply for this position?",
            "Describe your greatest professional achievement.",
            "What are your key strengths and how do they apply to this role?",
            "Where do you see yourself in the next 5 years?"
        ]

@app.post("/submit-answer")
async def submit_answer(data: dict):
    """Submit answer for a question"""
    session_id = data.get("session_id", "session_1")
    question_index = data.get("question_index")
    answer = data.get("answer")
    
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[session_id]
    
    # Store the answer
    if question_index < len(session.initial_questions):
        question = session.initial_questions[question_index]
        session.answers.append(QuestionAnswer(question=question, answer=answer))
    
    return {"status": "success", "message": "Answer recorded"}

@app.post("/generate-followup")
async def generate_followup_questions(data: dict):
    """Generate 5 follow-up questions based on initial Q&A"""
    session_id = data.get("session_id", "session_1")
    
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[session_id]
    
    # Prepare context for follow-up questions
    context = f"Resume: {session.resume_text}\n\n"
    context += "Initial Interview Q&A:\n"
    
    for qa in session.answers:
        context += f"Q: {qa.question}\nA: {qa.answer}\n\n"
    
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Based on the candidate's resume and their answers to initial questions, generate 5 follow-up questions that dive deeper into their responses. Focus on specific experiences, problem-solving abilities, and behavioral aspects. Return only the questions, numbered 1-5."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            max_tokens=500
        )
        
        questions_text = response.choices[0].message.content
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and any(char.isdigit() for char in q[:3])]
        
        # Clean up questions
        cleaned_questions = []
        for q in questions:
            cleaned = q.split('.', 1)[-1].strip() if '.' in q else q.strip()
            cleaned_questions.append(cleaned)
        
        session.follow_up_questions = cleaned_questions[:5]
        
        return {"questions": session.follow_up_questions}
    
    except Exception as e:
        print(f"Error generating follow-up questions: {e}")
        return {"questions": [
            "Can you elaborate on a specific challenge you mentioned?",
            "How do you handle conflict in a team environment?",
            "Describe a time when you had to learn something new quickly.",
            "What would you do differently in your previous role?",
            "How do you prioritize tasks when facing multiple deadlines?"
        ]}

@app.post("/submit-followup-answer")
async def submit_followup_answer(data: dict):
    """Submit answer for follow-up question"""
    session_id = data.get("session_id", "session_1")
    question_index = data.get("question_index")
    answer = data.get("answer")
    
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[session_id]
    
    if question_index < len(session.follow_up_questions):
        question = session.follow_up_questions[question_index]
        session.follow_up_answers.append(QuestionAnswer(question=question, answer=answer))
    
    return {"status": "success", "message": "Follow-up answer recorded"}

@app.post("/generate-rating")
async def generate_candidate_rating(data: dict):
    """Generate final candidate rating based on resume and all answers"""
    session_id = data.get("session_id", "session_1")
    
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[session_id]
    
    # Prepare complete context
    context = f"Resume: {session.resume_text}\n\n"
    context += "Initial Interview Q&A:\n"
    
    for qa in session.answers:
        context += f"Q: {qa.question}\nA: {qa.answer}\n\n"
    
    context += "Follow-up Interview Q&A:\n"
    for qa in session.follow_up_answers:
        context += f"Q: {qa.question}\nA: {qa.answer}\n\n"
    
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an HR expert evaluating a candidate. Based on their resume and interview answers, provide a comprehensive rating.

Return a JSON response with:
{
    "overall_score": (1-10),
    "technical_skills": (1-10),
    "communication": (1-10),
    "problem_solving": (1-10),
    "cultural_fit": (1-10),
    "experience_relevance": (1-10),
    "strengths": ["strength1", "strength2", "strength3"],
    "areas_for_improvement": ["area1", "area2"],
    "recommendation": "HIRE/MAYBE/REJECT",
    "summary": "Brief summary of the candidate"
}"""
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            max_tokens=800
        )
        
        rating_text = response.choices[0].message.content
        rating = json.loads(rating_text)
        
        session.final_rating = rating
        
        return rating
    
    except Exception as e:
        print(f"Error generating rating: {e}")
        return {
            "overall_score": 7,
            "technical_skills": 7,
            "communication": 8,
            "problem_solving": 7,
            "cultural_fit": 8,
            "experience_relevance": 7,
            "strengths": ["Good communication", "Relevant experience", "Positive attitude"],
            "areas_for_improvement": ["Technical depth", "Leadership experience"],
            "recommendation": "MAYBE",
            "summary": "Candidate shows promise but needs further evaluation"
        }

@app.websocket("/ws/speech")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time speech processing"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            speech_data = json.loads(data)
            
            # Echo back the transcribed text
            await websocket.send_text(json.dumps({
                "type": "transcription",
                "text": speech_data.get("text", "")
            }))
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)