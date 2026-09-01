import io
import os
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pypdf import PdfReader
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="InternWise BTech Suite", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

class DoubtRequest(BaseModel):
    query: str
    semester: str
    subject: str

class TestEvalRequest(BaseModel):
    subject: str
    question: str
    user_answer: str

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InternWise - B.Tech CSE Study & Career Hub</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2310b981' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .tab-btn.active { background-color: #10b981; color: #022c22; font-weight: 700; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <div class="max-w-6xl mx-auto px-4 py-8">
    
    <!-- Navbar / Header -->
    <header class="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-800 pb-6 mb-8">
      <div class="flex items-center gap-3.5">
        <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/30 text-slate-950">
          <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
        </div>
        <div>
          <h1 class="text-2xl font-extrabold tracking-tight">Intern<span class="text-emerald-400">Wise</span></h1>
          <p class="text-xs text-slate-400">B.Tech CSE Academic & AI Career Platform</p>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <nav class="flex flex-wrap gap-2 bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800 text-xs sm:text-sm">
        <button onclick="switchTab('notes')" id="tab-notes" class="tab-btn active px-4 py-2 rounded-xl transition">8 Sem Notes</button>
        <button onclick="switchTab('doubt')" id="tab-doubt" class="tab-btn px-4 py-2 rounded-xl text-slate-300 hover:text-white transition">AI Doubt Solver</button>
        <button onclick="switchTab('pyq')" id="tab-pyq" class="tab-btn px-4 py-2 rounded-xl text-slate-300 hover:text-white transition">PYQ Papers</button>
        <button onclick="switchTab('mock')" id="tab-mock" class="tab-btn px-4 py-2 rounded-xl text-slate-300 hover:text-white transition">Mock Test</button>
        <button onclick="switchTab('career')" id="tab-career" class="tab-btn px-4 py-2 rounded-xl text-slate-300 hover:text-white transition">Resume AI</button>
      </nav>
    </header>

    <!-- SECTION 1: 8 SEMESTER NOTES -->
    <section id="section-notes" class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold text-white">B.Tech CSE Semester Notes</h2>
          <p class="text-xs text-slate-400">Select semester to access syllabus, revision notes and key concepts</p>
        </div>
        <select id="semSelect" onchange="loadSemData()" class="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-emerald-400 font-semibold focus:outline-none focus:border-emerald-500">
          <option value="1">Semester 1 (Engineering Fundamentals)</option>
          <option value="2">Semester 2 (Programming & Electrical)</option>
          <option value="3">Semester 3 (DSA, Digital Logic, Discrete Math)</option>
          <option value="4">Semester 4 (OS, DBMS, Computer Org)</option>
          <option value="5">Semester 5 (DAA, Networks, Software Eng)</option>
          <option value="6">Semester 6 (Compiler, AI/ML, Cloud)</option>
          <option value="7">Semester 7 (Cybersecurity, Distributed Systems)</option>
          <option value="8">Semester 8 (Major Project & Industry Electives)</option>
        </select>
      </div>

      <div id="notesContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
    </section>

    <!-- SECTION 2: AI DOUBT SOLVER -->
    <section id="section-doubt" class="hidden space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5">
        <div>
          <h2 class="text-xl font-bold text-white">B.Tech AI Doubt & Problem Solver</h2>
          <p class="text-xs text-slate-400 mt-1">Ask questions, complex code debugs, algorithms, or derivation explanations</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <input type="text" id="doubtSem" placeholder="Semester (e.g., Sem 4)" class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none" />
          <input type="text" id="doubtSub" placeholder="Subject (e.g., Operating Systems / Algorithms)" class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none" />
        </div>

        <textarea id="doubtQuery" rows="4" placeholder="Paste your question, error log, or concept here..." class="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none resize-none"></textarea>

        <button onclick="askAIDoubt()" id="doubtBtn" class="w-full py-3.5 rounded-xl bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition cursor-pointer">Solve with AI Assistant</button>
      </div>

      <div id="doubtOutput" class="hidden bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
        <h3 class="text-sm font-bold text-emerald-400 uppercase">AI Explanation & Solution</h3>
        <div id="doubtSolutionText" class="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed"></div>
      </div>
    </section>

    <!-- SECTION 3: PYQ PAPERS -->
    <section id="section-pyq" class="hidden space-y-6">
      <div>
        <h2 class="text-xl font-bold text-white">Previous Year Question Papers (PYQs)</h2>
        <p class="text-xs text-slate-400">Download and practice university mid-term and end-term exam question papers</p>
      </div>
      <div id="pyqContainer" class="grid grid-cols-1 md:grid-cols-2 gap-5"></div>
    </section>

    <!-- SECTION 4: MOCK TESTS -->
    <section id="section-mock" class="hidden space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5">
        <div>
          <h2 class="text-xl font-bold text-white">Interactive Subject Mock Test</h2>
          <p class="text-xs text-slate-400 mt-1">Answer university standard questions and receive instant AI evaluation & grading</p>
        </div>

        <div class="flex flex-col sm:flex-row gap-4">
          <select id="mockSubject" class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none">
            <option value="Data Structures & Algorithms">Data Structures & Algorithms</option>
            <option value="Operating Systems">Operating Systems</option>
            <option value="Database Management Systems">Database Management Systems</option>
            <option value="Computer Networks">Computer Networks</option>
          </select>
          <button onclick="generateMockQuestion()" class="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-bold border border-slate-700">Generate Question</button>
        </div>

        <div id="mockQuestionCard" class="hidden bg-slate-950 p-5 rounded-2xl border border-slate-800 space-y-4">
          <span class="text-xs font-bold text-emerald-400 uppercase tracking-wide">Target Question:</span>
          <p id="activeQuestion" class="text-sm font-semibold text-white"></p>
          <textarea id="mockUserAnswer" rows="4" placeholder="Write your complete technical answer here..." class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"></textarea>
          <button onclick="submitMockAnswer()" id="mockSubmitBtn" class="px-5 py-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400">Evaluate Answer</button>
        </div>

        <div id="mockResultCard" class="hidden p-5 rounded-2xl bg-slate-950 border border-slate-800 text-sm space-y-2"></div>
      </div>
    </section>

    <!-- SECTION 5: ORIGINAL RESUME AI CAREER -->
    <section id="section-career" class="hidden space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
        <h2 class="text-xl font-bold text-white mb-4">Resume Gap Analysis & Interview Prep</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-2">Upload Resume (PDF)</label>
            <input type="file" id="resumeFile" accept=".pdf" class="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-emerald-500 file:text-slate-950 bg-slate-950 p-2 rounded-xl border border-slate-800" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-2">Target Job Description</label>
            <textarea id="jobDescription" rows="2" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none resize-none">Looking for a Software Engineering Intern with skills in Python, DSA, Git, and Web Development.</textarea>
          </div>
          <button type="button" id="submitBtn" onclick="runAnalysis()" class="w-full py-3.5 rounded-xl font-bold bg-emerald-500 text-slate-950 hover:bg-emerald-400 transition text-sm">Analyze Resume</button>
        </div>
      </div>

      <div id="results" class="hidden space-y-6">
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex justify-between items-center">
          <div>
            <span class="text-xs uppercase font-bold text-slate-400">Match Accuracy</span>
            <h3 class="text-xl font-bold text-white" id="resultFilename">Profile</h3>
          </div>
          <div class="text-4xl font-black text-emerald-400" id="matchScore">--%</div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h4 class="text-xs font-bold text-emerald-400 uppercase mb-3">Detected Skills</h4>
            <div id="detectedSkills" class="flex flex-wrap gap-2"></div>
          </div>
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h4 class="text-xs font-bold text-rose-400 uppercase mb-3">Missing Skills</h4>
            <div id="missingSkills" class="flex flex-wrap gap-2"></div>
          </div>
        </div>
      </div>
    </section>

  </div>

  <script>
    var semNotes = {
      1: [
        { name: "Engineering Mathematics I", topics: "Calculus, Matrices, Differential Equations", url: "#" },
        { name: "Engineering Physics", topics: "Optics, Quantum Mechanics, Laser & Fiber Optics", url: "#" },
        { name: "Basic Electrical Engg.", topics: "AC/DC Circuits, Transformers, Motors", url: "#" }
      ],
      2: [
        { name: "Programming in C", topics: "Pointers, Memory Allocation, Structures, File IO", url: "#" },
        { name: "Engineering Mathematics II", topics: "Fourier Series, Vector Calculus, Complex Numbers", url: "#" },
        { name: "Basic Electronics", topics: "Diodes, Transistors, Op-Amps, Logic Gates", url: "#" }
      ],
      3: [
        { name: "Data Structures & Algorithms", topics: "Arrays, Linked Lists, Trees, Graphs, Sorting", url: "#" },
        { name: "Digital Logic Design", topics: "K-Maps, Combinational & Sequential Circuits, Flip-Flops", url: "#" },
        { name: "Discrete Mathematics", topics: "Set Theory, Graph Theory, Combinatorics, Recurrences", url: "#" }
      ],
      4: [
        { name: "Operating Systems", topics: "Process Scheduling, Deadlocks, Virtual Memory, Linux CLI", url: "#" },
        { name: "Database Management (DBMS)", topics: "SQL Queries, Normalization (1NF-BCNF), Indexing, ACID", url: "#" },
        { name: "Computer Organization (COA)", topics: "Pipelining, Memory Hierarchy, ALU Design, Cache", url: "#" }
      ],
      5: [
        { name: "Design & Analysis of Algorithms", topics: "Divide & Conquer, Dynamic Programming, Greedy, NP-Hard", url: "#" },
        { name: "Computer Networks", topics: "OSI & TCP/IP Models, Routing Protocols, Sockets, Subnetting", url: "#" },
        { name: "Software Engineering", topics: "Agile, SDLC, Design Patterns, CI/CD Pipelines", url: "#" }
      ],
      6: [
        { name: "Compiler Design", topics: "Lexical Analysis, Parsing (LL/LR), Code Optimization", url: "#" },
        { name: "Artificial Intelligence & ML", topics: "Search Algos, Supervised/Unsupervised Learning, Neural Nets", url: "#" },
        { name: "Cloud Computing", topics: "AWS Basics, Microservices, Docker & Kubernetes", url: "#" }
      ],
      7: [
        { name: "Cybersecurity & Cryptography", topics: "RSA, AES, Network Security, Vulnerability Testing", url: "#" },
        { name: "Distributed Systems", topics: "Consensus (Raft/Paxos), RPC, Message Queues, Scalability", url: "#" },
        { name: "Big Data Analytics", topics: "Hadoop, Spark, MapReduce, NoSQL Architectures", url: "#" }
      ],
      8: [
        { name: "Major Project Documentation", topics: "SRS, High-Level Architecture, Viva Prep, Testing Reports", url: "#" },
        { name: "Industry Internship Electives", topics: "DevOps Practices, System Design, Production Readiness", url: "#" }
      ]
    };

    var pyqPapers = [
      { subject: "Data Structures & Algorithms", sem: "Semester 3", year: "2024 - End Term", marks: "100 Marks" },
      { subject: "Operating Systems", sem: "Semester 4", year: "2024 - Mid Term", marks: "50 Marks" },
      { subject: "Database Management Systems", sem: "Semester 4", year: "2023 - End Term", marks: "100 Marks" },
      { subject: "Computer Networks", sem: "Semester 5", year: "2024 - End Term", marks: "100 Marks" }
    ];

    function switchTab(tabName) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + tabName).classList.add('active');
      
      ['notes', 'doubt', 'pyq', 'mock', 'career'].forEach(sec => {
        document.getElementById('section-' + sec).classList.add('hidden');
      });
      document.getElementById('section-' + tabName).classList.remove('hidden');
    }

    function loadSemData() {
      var sem = document.getElementById('semSelect').value;
      var data = semNotes[sem] || [];
      var container = document.getElementById('notesContainer');
      var html = '';

      data.forEach(function(item) {
        html += '<div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between space-y-4 hover:border-emerald-500/40 transition">' +
          '<div>' +
            '<span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Semester ' + sem + '</span>' +
            '<h3 class="text-base font-bold text-white mt-1">' + item.name + '</h3>' +
            '<p class="text-xs text-slate-400 mt-2 leading-relaxed"><strong>Key Topics:</strong> ' + item.topics + '</p>' +
          '</div>' +
          '<button onclick="alert(\'Downloading Revision Notes for ' + item.name + '...\')" class="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700">Download Notes (PDF)</button>' +
        '</div>';
      });
      container.innerHTML = html;
    }

    function loadPyqs() {
      var container = document.getElementById('pyqContainer');
      var html = '';
      pyqPapers.forEach(function(p) {
        html += '<div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex items-center justify-between hover:border-emerald-500/40 transition">' +
          '<div>' +
            '<span class="text-xs font-bold text-emerald-400 uppercase">' + p.sem + '</span>' +
            '<h4 class="text-base font-bold text-white mt-0.5">' + p.subject + '</h4>' +
            '<p class="text-xs text-slate-400 mt-1">' + p.year + ' • ' + p.marks + '</p>' +
          '</div>' +
          '<button onclick="alert(\'Downloading ' + p.subject + ' PYQ Paper...\')" class="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-500 text-slate-950 hover:bg-emerald-400">Download</button>' +
        '</div>';
      });
      container.innerHTML = html;
    }

    async function askAIDoubt() {
      var query = document.getElementById('doubtQuery').value;
      var sem = document.getElementById('doubtSem').value || 'B.Tech CSE';
      var sub = document.getElementById('doubtSub').value || 'Computer Science';
      var btn = document.getElementById('doubtBtn');

      if (!query.trim()) { alert('Pehle apna doubt ya question type karein.'); return; }
      btn.disabled = true;
      btn.innerText = 'AI Assistant is solving...';

      try {
        var res = await fetch('/api/btech-doubt-solver', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query, semester: sem, subject: sub })
        });
        var data = await res.json();
        document.getElementById('doubtSolutionText').textContent = data.solution;
        document.getElementById('doubtOutput').classList.remove('hidden');
      } catch (err) {
        alert('Error solving doubt: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerText = 'Solve with AI Assistant';
      }
    }

    var sampleBank = {
      "Data Structures & Algorithms": "Explain the time complexity of QuickSort in Worst, Best and Average cases with the partition logic.",
      "Operating Systems": "What is Deadlock? List the four necessary Coffman conditions and explain Banker's Algorithm.",
      "Database Management Systems": "Explain the difference between 3NF and BCNF with a relational schema example.",
      "Computer Networks": "Explain the 3-Way Handshake mechanism in TCP connection establishment."
    };

    function generateMockQuestion() {
      var sub = document.getElementById('mockSubject').value;
      document.getElementById('activeQuestion').textContent = sampleBank[sub] || 'Explain key architecture concepts in ' + sub;
      document.getElementById('mockQuestionCard').classList.remove('hidden');
      document.getElementById('mockResultCard').classList.add('hidden');
      document.getElementById('mockUserAnswer').value = '';
    }

    async function submitMockAnswer() {
      var sub = document.getElementById('mockSubject').value;
      var q = document.getElementById('activeQuestion').textContent;
      var ans = document.getElementById('mockUserAnswer').value;
      var btn = document.getElementById('mockSubmitBtn');

      if (!ans.trim()) { alert('Pehle apna answer type karein.'); return; }
      btn.disabled = true;
      btn.innerText = 'AI Grading...';

      try {
        var res = await fetch('/api/evaluate-mock-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ subject: sub, question: q, user_answer: ans })
        });
        var data = await res.json();
        var out = document.getElementById('mockResultCard');
        out.innerHTML = '<div class="flex justify-between items-center"><span class="font-bold text-white">Score: <strong class="text-emerald-400">' + data.score + '/10</strong></span></div>' +
          '<p class="text-slate-300"><strong>Feedback:</strong> ' + data.feedback + '</p>' +
          '<p class="text-xs text-slate-400"><strong>Key Points Needed:</strong> ' + data.ideal_points + '</p>';
        out.classList.remove('hidden');
      } catch (e) {
        alert('Grading error: ' + e.message);
      } finally {
        btn.disabled = false;
        btn.innerText = 'Evaluate Answer';
      }
    }

    async function runAnalysis() {
      var fileInput = document.getElementById('resumeFile');
      var jobDesc = document.getElementById('jobDescription');
      var submitBtn = document.getElementById('submitBtn');

      if (!fileInput.files || fileInput.files.length === 0) { alert('PDF select karein.'); return; }
      submitBtn.disabled = true;
      submitBtn.innerText = 'Analyzing...';

      var formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('job_description', jobDesc.value);

      try {
        var res = await fetch('/api/analyze-resume', { method: 'POST', body: formData });
        var data = await res.json();
        var analysis = data.ai_analysis;
        document.getElementById('resultFilename').textContent = data.filename;
        document.getElementById('matchScore').textContent = (analysis.match_percentage || 0) + '%';
        
        var dHtml = '';
        (analysis.candidate_skills || []).forEach(s => dHtml += '<span class="px-3 py-1 text-xs rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">' + s + '</span>');
        document.getElementById('detectedSkills').innerHTML = dHtml;

        var mHtml = '';
        (analysis.missing_skills || []).forEach(s => mHtml += '<span class="px-3 py-1 text-xs rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">' + s + '</span>');
        document.getElementById('missingSkills').innerHTML = mHtml;

        document.getElementById('results').classList.remove('hidden');
      } catch (err) {
        alert('Error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Analyze Resume';
      }
    }

    // Init
    loadSemData();
    loadPyqs();
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def serve_home():
    return HTML_PAGE

@app.post("/api/btech-doubt-solver")
async def btech_doubt_solver(req: DoubtRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API Key Missing")
    
    prompt = f"""
    You are an expert Computer Science Professor and B.Tech Mentor.
    Subject: {req.subject}
    Semester: {req.semester}
    Student Question / Problem:
    {req.query}

    Provide an accurate, step-by-step, clean educational explanation with code/diagram references where applicable.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return {"solution": response.text}

@app.post("/api/evaluate-mock-test")
async def evaluate_mock_test(req: TestEvalRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API Key Missing")

    prompt = f"""
    Subject: {req.subject}
    Question: {req.question}
    Student Answer: {req.user_answer}

    Grade this answer out of 10 for a B.Tech university standard.
    Return ONLY a JSON object:
    {{
        "score": 8,
        "feedback": "2 sentences of objective feedback on accuracy and terminology",
        "ideal_points": "Key definitions, formulas or diagrams required for full marks"
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(response.text)

@app.post("/api/analyze-resume")
async def analyze_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API Key Missing")
    
    pdf_bytes = await file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    extracted_text = " ".join([page.extract_text() or "" for page in reader.pages]).strip()

    prompt = f"""
    Resume: {extracted_text}
    Job Description: {job_description}

    Return ONLY a JSON object:
    {{
        "candidate_skills": ["skill1", "skill2"],
        "missing_skills": ["missing1", "missing2"],
        "match_percentage": 80
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return {"filename": file.filename, "ai_analysis": json.loads(response.text)}