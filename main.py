import io, json, os, re, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sqlalchemy import create_engine, String, Text, Integer, DateTime, Boolean, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

load_dotenv()
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
PDF_DIR = DATA / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA / "internwise.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

class Base(DeclarativeBase): pass

class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    semester: Mapped[int] = mapped_column(Integer)
    branch: Mapped[str] = mapped_column(String(80), default="CSE")
    subject: Mapped[str] = mapped_column(String(150))
    resource_type: Mapped[str] = mapped_column(String(20))  # notes/pyq
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Bookmark(Base):
    __tablename__ = "bookmarks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user: Mapped[str] = mapped_column(String(150))
    resource_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

SUBJECTS = {
1:["Engineering Mathematics I","Engineering Physics","Programming for Problem Solving","Basic Electrical Engineering","Engineering Graphics"],
2:["Engineering Mathematics II","Engineering Chemistry","Data Structures","Digital Logic Design","Communication Skills"],
3:["Discrete Mathematics","Object Oriented Programming","Database Management Systems","Computer Organization","Operating Systems"],
4:["Design and Analysis of Algorithms","Computer Networks","Software Engineering","Theory of Computation","Web Technologies"],
5:["Compiler Design","Artificial Intelligence","Machine Learning","Cloud Computing","Professional Elective I"],
6:["Data Mining","Cyber Security","Distributed Systems","Mobile Application Development","Professional Elective II"],
7:["Deep Learning","Natural Language Processing","DevOps","Big Data Analytics","Professional Elective III"],
8:["Project","Internship/Industrial Training","Professional Elective IV","Seminar","Entrepreneurship"]
}

NOTE_TEMPLATE = """# {subject} — Semester {semester}\n\n## Quick Revision\n{subject} is an important B.Tech topic. This study pack gives a practical revision structure.\n\n## Unit-wise plan\n1. **Unit 1:** Fundamentals, definitions, terminology, important formulas/concepts.\n2. **Unit 2:** Core techniques, algorithms/processes, worked examples.\n3. **Unit 3:** Advanced concepts, comparisons and common exam questions.\n4. **Unit 4:** Applications, advantages, limitations and case studies.\n5. **Unit 5:** Revision, previous-question patterns and interview links.\n\n## Exam Focus\n- Learn definitions with one example.\n- Practice diagrams/algorithms wherever applicable.\n- Prepare 5-mark and 10-mark answers separately.\n- Solve at least two timed practice sets.\n\n## Viva / Interview\n- What problem does {subject} solve?\n- Explain its main concepts in simple language.\n- Give one real-world application.\n- Compare two related approaches.\n\n## Disclaimer\nThis is a demo revision pack. For university-specific notes, upload your verified PDF or configure the AI key to generate a subject-specific pack."""

app = FastAPI(title="InternWise Portal", version="12.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_KEY = os.getenv("ADMIN_KEY", "change-me")
client = None
if GEMINI_KEY:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_KEY)
    except Exception:
        client = None

class DoubtRequest(BaseModel):
    question: str = Field(min_length=2, max_length=8000)
    subject: str = "General B.Tech"
    semester: int = 1

class NotesGenRequest(BaseModel):
    semester: int
    subject: str
    units: int = Field(default=5, ge=1, le=8)

class Question(BaseModel):
    question: str
    marks: int = Field(default=2, ge=1, le=20)
    answer: Optional[str] = None

class TestEvalRequest(BaseModel):
    subject: str
    semester: int
    questions: list[Question]

class BookmarkRequest(BaseModel):
    user: str
    resource_id: int

class ResumeTextRequest(BaseModel):
    text: str = Field(min_length=20, max_length=50000)


def ai_text(prompt: str) -> Optional[str]:
    if not client: return None
    try:
        r = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return getattr(r, "text", None)
    except Exception:
        return None

def extract_json(text: str):
    text = text.strip().replace("```json", "").replace("```", "")
    m = re.search(r"\{.*\}", text, re.S)
    if not m: raise ValueError("No JSON")
    return json.loads(m.group(0))

def seed():
    with Session(engine) as s:
        if s.scalar(select(Resource.id).limit(1)):
            return
        for sem, subs in SUBJECTS.items():
            for sub in subs:
                s.add(Resource(title=f"{sub} — AI Revision Notes", semester=sem, subject=sub,
                    resource_type="notes", description="Demo revision notes; generate a fresh AI pack from the Notes tab.",
                    content=NOTE_TEMPLATE.format(subject=sub, semester=sem), is_demo=True))
                s.add(Resource(title=f"{sub} — Practice PYQ Set", semester=sem, subject=sub,
                    resource_type="pyq", year=2025, description="Demo practice questions. Replace with your university's verified PYQ PDFs.",
                    content=f"Practice PYQ Set — {sub}\n\n1. Define the core concepts of {sub}. (2 marks)\n2. Explain an important process/algorithm with diagram. (5 marks)\n3. Compare two major approaches in {sub}. (5 marks)\n4. Solve a representative problem and show steps. (10 marks)\n5. Discuss applications, advantages and limitations. (10 marks)", is_demo=True))
        s.commit()
seed()

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE.parent/"frontend"/"index.html").read_text(encoding="utf-8")

@app.get("/api/subjects")
def subjects(semester: int):
    if semester not in SUBJECTS: raise HTTPException(400, "Semester must be 1-8")
    return {"semester": semester, "subjects": SUBJECTS[semester]}

@app.get("/api/resources")
def resources(semester: Optional[int]=None, subject: Optional[str]=None, resource_type: Optional[str]=None):
    with Session(engine) as s:
        q = select(Resource).order_by(Resource.semester, Resource.subject, Resource.resource_type)
        if semester: q=q.where(Resource.semester==semester)
        if subject: q=q.where(Resource.subject==subject)
        if resource_type: q=q.where(Resource.resource_type==resource_type)
        rows=s.scalars(q).all()
        return [{"id":r.id,"title":r.title,"semester":r.semester,"subject":r.subject,"type":r.resource_type,"year":r.year,"description":r.description,"demo":r.is_demo,"has_file":bool(r.file_name)} for r in rows]

@app.get("/api/resources/{rid}")
def resource(rid:int):
    with Session(engine) as s:
        r=s.get(Resource,rid)
        if not r: raise HTTPException(404,"Resource not found")
        return {"id":r.id,"title":r.title,"semester":r.semester,"subject":r.subject,"type":r.resource_type,"year":r.year,"description":r.description,"content":r.content,"file_url":f"/api/resources/{rid}/file" if r.file_name else None,"demo":r.is_demo}

@app.get("/api/resources/{rid}/file")
def resource_file(rid:int):
    with Session(engine) as s:
        r=s.get(Resource,rid)
        if not r or not r.file_name: raise HTTPException(404,"PDF not found")
        path=PDF_DIR/r.file_name
        if not path.exists(): raise HTTPException(404,"PDF missing")
        return FileResponse(path, media_type="application/pdf", filename=path.name)

@app.post("/api/resources/upload")
async def upload_resource(x_admin_key: str = Header(default=""), semester:int=Form(...), subject:str=Form(...), resource_type:str=Form(...), title:str=Form(...), year:Optional[int]=Form(None), description:str=Form(""), pdf:UploadFile=File(...)):
    if x_admin_key != ADMIN_KEY: raise HTTPException(401,"Invalid admin key")
    if resource_type not in {"notes","pyq"}: raise HTTPException(400,"resource_type must be notes or pyq")
    if pdf.content_type != "application/pdf": raise HTTPException(400,"Only PDF files are allowed")
    data=await pdf.read()
    if len(data)>15*1024*1024: raise HTTPException(413,"PDF must be <=15 MB")
    name=f"{uuid.uuid4().hex}.pdf"; (PDF_DIR/name).write_bytes(data)
    with Session(engine) as s:
        r=Resource(title=title,semester=semester,subject=subject,resource_type=resource_type,year=year,description=description,file_name=name,is_demo=False)
        s.add(r); s.commit(); s.refresh(r)
        return {"ok":True,"id":r.id,"file_url":f"/api/resources/{r.id}/file"}

@app.post("/api/generate-full-notes")
def generate_notes(req: NotesGenRequest):
    if req.semester not in SUBJECTS: raise HTTPException(400,"Semester must be 1-8")
    prompt=f"Create exam-ready B.Tech notes for {req.subject}, semester {req.semester}. Use {req.units} units. Include definitions, explanations, formulas/algorithms where relevant, examples, common mistakes, 2/5/10-mark questions and viva questions. Markdown only, concise but useful."
    text=ai_text(prompt) or NOTE_TEMPLATE.format(subject=req.subject, semester=req.semester)
    return {"subject":req.subject,"semester":req.semester,"content":text,"ai":bool(client)}

@app.post("/api/btech-doubt-solver")
def doubt(req:DoubtRequest):
    prompt=f"You are a B.Tech tutor. Subject: {req.subject}; Semester: {req.semester}. Answer this doubt clearly. Start with a one-line answer, then explain step-by-step, give a small example, and end with 2 exam tips. Question: {req.question}"
    answer=ai_text(prompt) or f"### Short answer\nYour doubt is about **{req.subject}**.\n\n### Step-by-step\n1. Identify the definition/concept involved.\n2. Break the problem into smaller parts.\n3. Apply the relevant formula, rule or algorithm.\n4. Verify the result with an example.\n\n### Exam tip\nWrite the definition first, then steps/diagram, then a conclusion.\n\n*AI key not configured, so this is fallback tutor guidance.*"
    return {"answer":answer,"ai":bool(client)}

@app.post("/api/evaluate-mock-test")
def evaluate(req:TestEvalRequest):
    answered=sum(1 for q in req.questions if (q.answer or '').strip())
    total=len(req.questions)
    score=round(answered/total*100) if total else 0
    ai_feedback=None
    if client:
        prompt="Evaluate these B.Tech mock-test answers. Return JSON with score_percent (0-100), strengths(array), weaknesses(array), study_plan(array), feedback(string). Be strict but constructive.\n"+json.dumps(req.model_dump())
        try: ai_feedback=extract_json(ai_text(prompt) or "")
        except Exception: ai_feedback=None
    if not ai_feedback:
        ai_feedback={"score_percent":score,"strengths":["Attempted questions" if answered else "Start attempting questions"],"weaknesses":["Answers need topic-specific checking in fallback mode"],"study_plan":[f"Revise {req.subject} core concepts","Practice 10 previous questions","Take another timed mock"],"feedback":f"You attempted {answered}/{total} questions. Configure GEMINI_API_KEY for detailed AI answer-by-answer evaluation."}
    return ai_feedback | {"ai":bool(client)}

@app.post("/api/analyze-resume")
async def analyze_resume(pdf: UploadFile=File(...)):
    if pdf.content_type != "application/pdf": raise HTTPException(400,"Upload a PDF resume")
    data=await pdf.read()
    if len(data)>10*1024*1024: raise HTTPException(413,"Resume must be <=10 MB")
    try:
        reader=PdfReader(io.BytesIO(data)); text="\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e: raise HTTPException(400,f"Could not read PDF: {e}")
    if len(text.strip())<30: raise HTTPException(400,"Could not extract enough text. Upload a text-based PDF.")
    prompt="""Analyze this B.Tech student's resume for internships/jobs in India. Return JSON only with: quality_score (0-100), summary, strengths(array), missing_skills(array), priority_skills(array), projects_to_build(array), ats_tips(array), suitable_roles(array), companies(array of objects with name, reason, estimated_package, platform), platforms(array of objects with name, search_url_hint), salary_estimate (string), 30_day_plan(array). Do not claim a guaranteed salary/job. Keep package as a realistic approximate range and explain that it varies. Resume:\n"""+text[:45000]
    result=None
    if client:
        try: result=extract_json(ai_text(prompt) or "")
        except Exception: result=None
    if not result:
        low=text.lower()
        skills=[]
        for k in ["python","java","c++","c","javascript","react","sql","html","css","git","fastapi","machine learning","data structures","aws"]:
            if k in low: skills.append(k)
        missing=[k for k in ["dsa","sql","git","projects","communication","aptitude"] if k not in low]
        result={"quality_score":65,"summary":"Decent starting resume; strengthen evidence of projects, measurable outcomes and job-ready skills.","strengths":skills[:6] or ["B.Tech profile"],"missing_skills":missing,"priority_skills":missing[:4],"projects_to_build":["One full-stack project","One DSA/problem-solving project","Deploy one project and add GitHub link"],"ats_tips":["Use a clean one-page format","Add measurable results","Match keywords to each job description"],"suitable_roles":["Software Developer Intern","Web Developer Intern","Graduate Software Engineer"],"companies":[{"name":"TCS","reason":"Large graduate hiring ecosystem","estimated_package":"~₹3–7 LPA","platform":"Naukri/LinkedIn"},{"name":"Infosys","reason":"Graduate and fresher opportunities","estimated_package":"~₹3.5–7 LPA","platform":"LinkedIn/Official careers"},{"name":"Accenture","reason":"Technology and analyst roles","estimated_package":"~₹4–8 LPA","platform":"Naukri/LinkedIn"}],"platforms":[{"name":"LinkedIn","search_url_hint":"Search your role + internship/fresher"},{"name":"Naukri","search_url_hint":"Search B.Tech fresher + role"},{"name":"Internshala","search_url_hint":"Search software development internships"}],"salary_estimate":"For a fresher, roughly ₹3–8 LPA is a broad starting range; skills, location and company can move this substantially.","30_day_plan":["Week 1: DSA + SQL","Week 2: Build/deploy project","Week 3: Resume + GitHub + LinkedIn","Week 4: Apply to 10–15 targeted roles/day and practice interviews"]}
    return result | {"ai":bool(client),"extracted_chars":len(text)}

@app.post("/api/bookmarks")
def add_bookmark(req:BookmarkRequest):
    with Session(engine) as s:
        if not s.get(Resource,req.resource_id): raise HTTPException(404,"Resource not found")
        existing=s.scalar(select(Bookmark).where(Bookmark.user==req.user,Bookmark.resource_id==req.resource_id))
        if not existing: s.add(Bookmark(user=req.user,resource_id=req.resource_id)); s.commit()
        return {"ok":True}

@app.delete("/api/bookmarks")
def remove_bookmark(user:str, resource_id:int):
    with Session(engine) as s:
        b=s.scalar(select(Bookmark).where(Bookmark.user==user,Bookmark.resource_id==resource_id))
        if b: s.delete(b); s.commit()
        return {"ok":True}

@app.get("/api/bookmarks")
def list_bookmarks(user:str):
    with Session(engine) as s:
        ids=[b.resource_id for b in s.scalars(select(Bookmark).where(Bookmark.user==user)).all()]
        return {"resource_ids":ids}

@app.get("/api/health")
def health(): return {"status":"ok","ai_configured":bool(client),"database":DB_PATH.exists()}