from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pypdf import PdfReader
from google import genai
from google.genai import types
import io
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="InternWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

class AnswerEvaluationRequest(BaseModel):
    question: str
    user_answer: str

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InternWise - AI Career Intelligence</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    @media print {
      body { background: white !important; color: black !important; }
      .no-print { display: none !important; }
      .print-card { border: 1px solid #e2e8f0 !important; background: white !important; color: black !important; }
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <div class="max-w-5xl mx-auto px-6 py-12">
    
    <!-- Header -->
    <header class="text-center mb-10 no-print">
      <span class="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        AI Career Intelligence Platform
      </span>
      <h1 class="text-4xl sm:text-5xl font-extrabold mt-4 tracking-tight">Intern<span class="text-emerald-400">Wise</span></h1>
      <p class="text-slate-400 mt-2 text-base">Instant resume gap analysis, personalized skill roadmap & interview prep</p>
    </header>

    <!-- Upload Box -->
    <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl mb-10 no-print">
      <div class="space-y-6">
        <div>
          <label class="block text-sm font-semibold text-slate-300 mb-2">Upload Resume (PDF)</label>
          <input type="file" id="resumeFile" accept=".pdf" 
            class="w-full text-sm text-slate-400 file:mr-4 file:py-2.5 file:px-5 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-500 file:text-slate-950 hover:file:bg-emerald-400 cursor-pointer bg-slate-950/60 p-2.5 rounded-2xl border border-slate-800" />
        </div>

        <div>
          <label class="block text-sm font-semibold text-slate-300 mb-2">Target Job Description</label>
          <textarea id="jobDescription" rows="3" class="w-full bg-slate-950/60 border border-slate-800 rounded-2xl p-4 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 resize-none">Looking for a Software Engineering Intern with skills in Python, JavaScript, Data Structures, and Git.</textarea>
        </div>

        <button type="button" id="submitBtn" onclick="runAnalysis()"
          class="w-full py-4 px-6 rounded-2xl font-bold bg-emerald-500 text-slate-950 hover:bg-emerald-400 active:scale-[0.99] transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 cursor-pointer">
          <span id="btnText">Analyze Resume with AI</span>
        </button>
      </div>
    </div>

    <!-- Results Section -->
    <div id="results" class="hidden space-y-6">
      
      <div class="flex items-center justify-between no-print">
        <h2 class="text-xl font-bold text-white">Analysis Report</h2>
        <button onclick="window.print()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-2 cursor-pointer">
          <span>Download / Print PDF Report</span>
        </button>
      </div>

      <!-- Match Score -->
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 print-card">
        <div>
          <span class="text-xs uppercase font-bold tracking-wider text-slate-400">Match Accuracy</span>
          <h3 class="text-2xl font-bold text-white mt-1" id="resultFilename">Candidate Profile</h3>
          <p class="text-sm text-slate-400 mt-1">Evaluated against target role requirements</p>
        </div>
        <div class="text-5xl font-black text-emerald-400" id="matchScore">--%</div>
      </div>

      <!-- Skills Detected vs Missing -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 print-card">
          <h4 class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-4">Detected Skills in Resume</h4>
          <div id="detectedSkills" class="flex flex-wrap gap-2"></div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 print-card">
          <h4 class="text-xs font-bold text-rose-400 uppercase tracking-wider mb-4">Missing Skills Required</h4>
          <div id="missingSkills" class="flex flex-wrap gap-2"></div>
        </div>
      </div>

      <!-- Roadmap & Project -->
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 print-card">
        <div>
          <h4 class="text-base font-bold text-emerald-400 mb-3">2-Week Fast-Track Learning Roadmap</h4>
          <div id="roadmapList" class="space-y-3 text-sm text-slate-300"></div>
        </div>

        <hr class="border-slate-800" />

        <div>
          <h4 class="text-base font-bold text-emerald-400 mb-3">Recommended Resume-Boosting Project</h4>
          <div id="projectIdea" class="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 text-sm text-slate-300"></div>
        </div>
      </div>

      <!-- Resume Improvement Points -->
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 print-card">
        <h4 class="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3">Resume Improvement Points</h4>
        <ul id="feedbackList" class="list-disc list-inside space-y-2 text-sm text-slate-300"></ul>
      </div>

      <!-- Interactive Mock Interview Questions -->
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 print-card">
        <div>
          <h4 class="text-lg font-bold text-emerald-400">Interactive AI Mock Interview</h4>
          <p class="text-xs text-slate-400 mt-1">Type your answer below and submit to get real-time AI scoring & model answers.</p>
        </div>
        <div id="interviewQuestionsContainer" class="space-y-6"></div>
      </div>

    </div>
  </div>

  <script>
    var globalQuestions = [];

    async function runAnalysis() {
      var fileInput = document.getElementById('resumeFile');
      var jobDesc = document.getElementById('jobDescription');
      var submitBtn = document.getElementById('submitBtn');
      var btnText = document.getElementById('btnText');
      var resultsDiv = document.getElementById('results');

      if (!fileInput.files || fileInput.files.length === 0) {
        alert('Kripya pehle apni Resume PDF select karein.');
        return;
      }

      submitBtn.disabled = true;
      btnText.textContent = 'Analyzing with Gemini AI... Please wait...';

      var formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('job_description', jobDesc.value);

      try {
        var res = await fetch('/api/analyze-resume', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          var errJson = await res.json();
          throw new Error(errJson.detail || 'Server error');
        }

        var data = await res.json();
        var analysis = data.ai_analysis;
        globalQuestions = analysis.interview_prep_questions || [];

        document.getElementById('resultFilename').textContent = data.filename;
        document.getElementById('matchScore').textContent = (analysis.match_percentage || 0) + '%';

        var detectedHtml = '';
        (analysis.candidate_skills || []).forEach(function(s) {
          detectedHtml += '<span class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">' + s + '</span>';
        });
        document.getElementById('detectedSkills').innerHTML = detectedHtml;

        var missingHtml = '';
        (analysis.missing_skills || []).forEach(function(s) {
          missingHtml += '<span class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">' + s + '</span>';
        });
        document.getElementById('missingSkills').innerHTML = missingHtml;

        var roadmapHtml = '';
        (analysis.learning_roadmap || []).forEach(function(step, idx) {
          roadmapHtml += '<div class="flex items-start gap-3"><span class="font-bold text-emerald-400">Step ' + (idx + 1) + ':</span> <span>' + step + '</span></div>';
        });
        document.getElementById('roadmapList').innerHTML = roadmapHtml;

        var project = analysis.recommended_project || {};
        document.getElementById('projectIdea').innerHTML = '<strong>' + (project.title || 'Project') + ':</strong> ' + (project.description || 'Build a portfolio project.');

        var feedbackHtml = '';
        (analysis.resume_feedback || []).forEach(function(f) {
          feedbackHtml += '<li>' + f + '</li>';
        });
        document.getElementById('feedbackList').innerHTML = feedbackHtml;

        var questionsHtml = '';
        globalQuestions.forEach(function(q, idx) {
          questionsHtml += '<div class="bg-slate-950/70 p-5 rounded-2xl border border-slate-800 space-y-3">' +
            '<div class="flex items-start gap-3">' +
              '<span class="px-2.5 py-1 text-xs font-bold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Q' + (idx + 1) + '</span>' +
              '<p class="text-sm font-semibold text-slate-200">' + q + '</p>' +
            '</div>' +
            '<textarea id="answerInput_' + idx + '" rows="2" placeholder="Type your answer here..." class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 resize-none"></textarea>' +
            '<div class="flex justify-end">' +
              '<button onclick="evaluateAnswer(' + idx + ')" id="evalBtn_' + idx + '" class="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-500 text-slate-950 hover:bg-emerald-400 transition-all cursor-pointer">' +
                'Submit for AI Evaluation' +
              '</button>' +
            '</div>' +
            '<div id="feedbackResult_' + idx + '" class="hidden mt-3 p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm space-y-2"></div>' +
          '</div>';
        });
        document.getElementById('interviewQuestionsContainer').innerHTML = questionsHtml;

        resultsDiv.classList.remove('hidden');
        resultsDiv.scrollIntoView({ behavior: 'smooth' });
      } catch (err) {
        alert('Analysis Error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        btnText.textContent = 'Analyze Resume with AI';
      }
    }

    async function evaluateAnswer(idx) {
      var q = globalQuestions[idx];
      var answerInput = document.getElementById('answerInput_' + idx);
      var btn = document.getElementById('evalBtn_' + idx);
      var resultBox = document.getElementById('feedbackResult_' + idx);

      if (!answerInput.value.trim()) {
        alert('Pehle apna answer type karein.');
        return;
      }

      btn.disabled = true;
      btn.innerText = 'Grading with AI...';

      try {
        var res = await fetch('/api/evaluate-answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, user_answer: answerInput.value })
        });

        var data = await res.json();
        var evalData = data.evaluation;

        resultBox.innerHTML = '<div class="flex items-center justify-between">' +
          '<span class="font-bold text-white">AI Score: <span class="text-emerald-400 font-extrabold">' + evalData.score + '/10</span></span>' +
          '</div>' +
          '<p class="text-slate-300"><strong>Feedback:</strong> ' + evalData.feedback + '</p>' +
          '<div class="pt-2 border-t border-slate-800 text-xs text-slate-400">' +
            '<strong class="text-emerald-400">Ideal Answer Key:</strong> ' + evalData.ideal_answer_hint +
          '</div>';
        resultBox.classList.remove('hidden');
      } catch (err) {
        alert('Evaluation error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerText = 'Re-evaluate';
      }
    }
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def serve_home():
    return HTML_PAGE

@app.post("/api/analyze-resume")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form("Software Development Internship")
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sirf PDF files allowed hain.")

    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY nahi mili .env file mein.")

    try:
        pdf_bytes = await file.read()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = " ".join([page.extract_text() or "" for page in reader.pages]).strip()

        if not extracted_text:
            raise HTTPException(status_code=400, detail="PDF se text extract nahi ho saka.")

        prompt = f"""
        You are an elite technical mentor and hiring expert.
        Analyze this candidate resume against the given target job description.

        Resume Content:
        {extracted_text}

        Target Job Description:
        {job_description}

        Return a JSON object with this exact structure:
        {{
            "candidate_skills": ["list of skills extracted from resume"],
            "required_skills": ["key skills needed for this job description"],
            "missing_skills": ["skills required for the job but missing in resume"],
            "match_percentage": 75,
            "learning_roadmap": [
                "Week 1: Master missing fundamentals",
                "Week 1: Practice core algorithmic concepts",
                "Week 2: Build practical feature implementations",
                "Week 2: Deploy and integrate with Git"
            ],
            "recommended_project": {{
                "title": "Project Title",
                "description": "Short explanation of a practical project covering missing skills"
            }},
            "resume_feedback": ["2-3 concrete tips to improve the resume"],
            "interview_prep_questions": ["3-4 technical questions to prepare based on missing/required skills"]
        }}
        """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return {
            "filename": file.filename,
            "ai_analysis": json.loads(response.text)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate-answer")
async def evaluate_answer(req: AnswerEvaluationRequest):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    try:
        prompt = f"""
        Evaluate this candidate's interview answer:
        Question: {req.question}
        Candidate Answer: {req.user_answer}

        Return a JSON object with this exact structure:
        {{
            "score": 8,
            "feedback": "2-3 concise sentences grading accuracy, clarity, and depth",
            "ideal_answer_hint": "Key points that make a 10/10 answer"
        }}
        """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return {"evaluation": json.loads(response.text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))