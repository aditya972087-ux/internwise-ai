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

app = FastAPI(title="InternWise Student & Career Portal", version="3.4.0")

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
    course: str
    branch: str
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
  <title>InternWise - Student Academic & Career Portal</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2310b981' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .tab-btn.active { background: linear-gradient(135deg, #10b981, #059669); color: #022c22; font-weight: 800; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

  <div id="onboardingScreen" class="min-h-screen flex items-center justify-center p-4">
    <div class="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl space-y-6">
      
      <div class="text-center space-y-2">
        <div class="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/30 text-slate-950">
          <svg class="w-8 h-8 text-slate-950" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
        </div>
        <h1 class="text-3xl font-black tracking-tight">Intern<span class="text-emerald-400">Wise</span></h1>
        <p class="text-xs sm:text-sm text-slate-400">Student Academic Portal & Career AI Suite</p>
      </div>

      <div class="border-t border-slate-800 pt-4">
        <h2 class="text-lg font-bold text-white mb-1">Create Student Profile</h2>
        <p class="text-xs text-slate-400">Fill details to personalize your study notes, mock tests & career AI.</p>
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
          <input type="text" id="userName" value="Aditya Kumar" placeholder="e.g. Rahul Sharma" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-white focus:border-emerald-500 focus:outline-none" />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
            <input type="email" id="userEmail" value="aditya972087@gmail.com" placeholder="rahul@example.com" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-white focus:border-emerald-500 focus:outline-none" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Mobile Number</label>
            <input type="text" id="userPhone" value="9389033360" placeholder="+91 9876543210" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-white focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Gender</label>
            <select id="userGender" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-white focus:border-emerald-500 focus:outline-none">
              <option value="Male" selected>Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Age</label>
            <input type="number" id="userAge" value="18" placeholder="e.g. 20" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-white focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1">Academic Status</label>
          <select id="userStatus" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-emerald-400 font-semibold focus:border-emerald-500 focus:outline-none">
            <option value="Currently Pursuing B.Tech / BE" selected>Currently Pursuing B.Tech / BE</option>
            <option value="Currently Pursuing BCA / MCA">Currently Pursuing BCA / MCA</option>
            <option value="Currently Pursuing Diploma">Currently Pursuing Diploma / Polytechnic</option>
            <option value="Completed Degree / Graduate">Completed Course / Graduate</option>
          </select>
        </div>

        <button type="button" onclick="goToDashboardDirect()" id="enterPortalBtn" class="w-full py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-black text-sm transition shadow-lg shadow-emerald-500/20 cursor-pointer">
          Enter InternWise Portal &rarr;
        </button>
      </div>
    </div>
  </div>


  <div id="mainDashboard" class="hidden max-w-6xl mx-auto px-4 py-6">
    
    <header class="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-800 pb-6 mb-8">
      <div class="flex items-center gap-3.5">
        <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/30 text-slate-950">
          <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-black tracking-tight">Intern<span class="text-emerald-400">Wise</span></h1>
            <span class="px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PRO</span>
          </div>
          <p class="text-xs text-slate-400">Welcome, <strong id="greetingName" class="text-white">Aditya Kumar</strong> (<span id="greetingStatus" class="text-emerald-400">B.Tech</span>)</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <nav class="flex flex-wrap gap-1.5 bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800 text-xs sm:text-sm">
          <button onclick="switchTab('notes')" id="tab-notes" class="tab-btn active px-3 sm:px-4 py-2 rounded-xl transition cursor-pointer">Notes Hub</button>
          <button onclick="switchTab('doubt')" id="tab-doubt" class="tab-btn px-3 sm:px-4 py-2 rounded-xl text-slate-300 hover:text-white transition cursor-pointer">AI Doubt Solver</button>
          <button onclick="switchTab('pyq')" id="tab-pyq" class="tab-btn px-3 sm:px-4 py-2 rounded-xl text-slate-300 hover:text-white transition cursor-pointer">PYQs</button>
          <button onclick="switchTab('mock')" id="tab-mock" class="tab-btn px-3 sm:px-4 py-2 rounded-xl text-slate-300 hover:text-white transition cursor-pointer">Mock Test</button>
          <button onclick="switchTab('career')" id="tab-career" class="tab-btn px-3 sm:px-4 py-2 rounded-xl text-slate-300 hover:text-white transition cursor-pointer">Job & Career</button>
        </nav>
        
        <button onclick="logoutProfile()" title="Change Profile" class="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white text-xs cursor-pointer">
          &#x21bb; Switch
        </button>
      </div>
    </header>

    <section id="section-notes" class="space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white">Academic Notes & Syllabus Finder</h2>
          <p class="text-xs text-slate-400 mt-1">Select course, branch, and semester to view verified notes.</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">1. Select Course</label>
            <select id="notesCourse" onchange="filterNotes()" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-emerald-400 font-semibold focus:border-emerald-500 focus:outline-none">
              <option value="B.Tech">B.Tech / B.E.</option>
              <option value="BCA">BCA</option>
              <option value="MCA">MCA</option>
              <option value="Diploma">Diploma (Polytechnic)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">2. Select Branch</label>
            <select id="notesBranch" onchange="filterNotes()" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-slate-200 focus:border-emerald-500 focus:outline-none">
              <option value="CSE">Computer Science & Engg (CSE)</option>
              <option value="IT">Information Technology (IT)</option>
              <option value="AIML">AI & Machine Learning</option>
              <option value="ECE">Electronics & Communication (ECE)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">3. Select Semester</label>
            <select id="notesSem" onchange="filterNotes()" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-slate-200 focus:border-emerald-500 focus:outline-none">
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
              <option value="3" selected>Semester 3</option>
              <option value="4">Semester 4</option>
              <option value="5">Semester 5</option>
              <option value="6">Semester 6</option>
              <option value="7">Semester 7</option>
              <option value="8">Semester 8</option>
            </select>
          </div>
        </div>
      </div>

      <div id="notesCardsList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
    </section>

    <section id="section-doubt" class="hidden space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5">
        <div>
          <h2 class="text-xl font-bold text-white">24/7 AI Problem & Doubt Assistant</h2>
          <p class="text-xs text-slate-400 mt-1">Get instant step-by-step solutions and code debugging.</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input type="text" id="askCourse" placeholder="Course (e.g. B.Tech)" class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none" />
          <input type="text" id="askBranch" placeholder="Branch (e.g. CSE / IT)" class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none" />
          <input type="text" id="askSubject" placeholder="Subject (e.g. DBMS / OS / DSA)" class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none" />
        </div>

        <textarea id="askQuery" rows="4" placeholder="Paste your question or doubt here..." class="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs sm:text-sm text-slate-200 focus:border-emerald-500 focus:outline-none resize-none"></textarea>

        <button onclick="askDoubtAI()" id="doubtSubmitBtn" class="w-full py-3.5 rounded-xl bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition cursor-pointer">
          Solve with AI Assistant
        </button>
      </div>

      <div id="doubtSolutionBox" class="hidden bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4">
        <h3 class="text-sm font-bold text-emerald-400 uppercase tracking-wider">AI Solution</h3>
        <div id="doubtSolutionText" class="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed"></div>
      </div>
    </section>

    <section id="section-pyq" class="hidden space-y-6">
      <div>
        <h2 class="text-xl font-bold text-white">Previous Year Question Papers (PYQs)</h2>
        <p class="text-xs text-slate-400">Download and solve past university exam papers</p>
      </div>
      <div id="pyqList" class="grid grid-cols-1 md:grid-cols-2 gap-5"></div>
    </section>

    <section id="section-mock" class="hidden space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5">
        <div>
          <h2 class="text-xl font-bold text-white">Subject Mock Test & AI Evaluator</h2>
          <p class="text-xs text-slate-400 mt-1">Generate questions and receive instant AI grading.</p>
        </div>

        <div class="flex flex-col sm:flex-row gap-4">
          <select id="mockSubjectPick" class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none">
            <option value="Data Structures & Algorithms">Data Structures & Algorithms (DSA)</option>
            <option value="Operating Systems">Operating Systems (OS)</option>
            <option value="Database Management Systems">Database Management Systems (DBMS)</option>
            <option value="Computer Networks">Computer Networks (CN)</option>
          </select>
          <button onclick="generateMockQ()" class="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-bold border border-slate-700 cursor-pointer">Generate Question</button>
        </div>

        <div id="mockQuestionArea" class="hidden bg-slate-950 p-5 rounded-2xl border border-slate-800 space-y-4">
          <span class="text-xs font-bold text-emerald-400 uppercase tracking-wide">University Question:</span>
          <p id="mockQuestionText" class="text-sm font-semibold text-white"></p>
          <textarea id="mockUserAns" rows="4" placeholder="Write your answer here..." class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"></textarea>
          <button onclick="submitMockGrading()" id="mockGradingBtn" class="px-5 py-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400 cursor-pointer">Evaluate My Answer</button>
        </div>

        <div id="mockEvaluationResult" class="hidden p-5 rounded-2xl bg-slate-950 border border-slate-800 text-sm space-y-2"></div>
      </div>
    </section>

    <section id="section-career" class="hidden space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-5">
        <div>
          <h2 class="text-xl font-bold text-white">Job Requirements & Resume Gap Analysis</h2>
          <p class="text-xs text-slate-400 mt-1">Upload resume to match against job descriptions.</p>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-2">Upload Resume (PDF)</label>
            <input type="file" id="resumeFile" accept=".pdf" class="w-full text-xs text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-emerald-500 file:text-slate-950 bg-slate-950 p-2 rounded-xl border border-slate-800" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-2">Target Job Description</label>
            <textarea id="jobDescription" rows="3" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-slate-200 focus:border-emerald-500 focus:outline-none resize-none">Looking for a Software Development Engineer (SDE) Intern with proficiency in Python/Java, Data Structures, SQL, and Git.</textarea>
          </div>

          <button type="button" id="careerAnalyzeBtn" onclick="runResumeAnalysis()" class="w-full py-3.5 rounded-xl font-bold bg-emerald-500 text-slate-950 hover:bg-emerald-400 transition text-sm cursor-pointer">
            Analyze Resume Match with AI
          </button>
        </div>
      </div>

      <div id="careerResults" class="hidden space-y-6">
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div>
            <span class="text-xs uppercase font-bold text-slate-400">Match Accuracy</span>
            <h3 class="text-xl font-bold text-white" id="careerFilename">Resume Profile</h3>
          </div>
          <div class="text-4xl font-black text-emerald-400" id="careerMatchScore">--%</div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h4 class="text-xs font-bold text-emerald-400 uppercase mb-3">Detected Skills</h4>
            <div id="careerDetectedSkills" class="flex flex-wrap gap-2"></div>
          </div>
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h4 class="text-xs font-bold text-rose-400 uppercase mb-3">Missing Skills</h4>
            <div id="careerMissingSkills" class="flex flex-wrap gap-2"></div>
          </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4">
          <h4 class="text-base font-bold text-emerald-400">2-Week Learning Roadmap</h4>
          <div id="careerRoadmap" class="space-y-2 text-sm text-slate-300"></div>
        </div>
      </div>
    </section>

  </div>

  <script>
    // Bullet-proof Direct Screen Switching
    function goToDashboardDirect() {
      var nameVal = (document.getElementById('userName').value || 'Aditya Kumar').trim();
      var statusVal = document.getElementById('userStatus').value || 'Currently Pursuing B.Tech / BE';

      // Update text
      document.getElementById('greetingName').innerText = nameVal;
      document.getElementById('greetingStatus').innerText = statusVal;

      // Force Remove Class and Hide Element
      var onb = document.getElementById('onboardingScreen');
      var dash = document.getElementById('mainDashboard');

      onb.classList.add('hidden');
      onb.style.display = 'none';

      dash.classList.remove('hidden');
      dash.style.display = 'block';

      // Load Content
      filterNotes();
      loadPyqList();

      try {
        localStorage.setItem('internwise_user', JSON.stringify({ name: nameVal, status: statusVal }));
      } catch(e) {}
    }

    // Auto check if already saved
    window.onload = function() {
      try {
        var saved = localStorage.getItem('internwise_user');
        if (saved) {
          var u = JSON.parse(saved);
          if (u && u.name) {
            document.getElementById('userName').value = u.name;
            goToDashboardDirect();
          }
        }
      } catch (e) {}
    };

    function logoutProfile() {
      try { localStorage.removeItem('internwise_user'); } catch(e) {}
      location.reload();
    }

    function switchTab(tabName) {
      document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
      var activeBtn = document.getElementById('tab-' + tabName);
      if (activeBtn) activeBtn.classList.add('active');

      ['notes', 'doubt', 'pyq', 'mock', 'career'].forEach(function(s) {
        var el = document.getElementById('section-' + s);
        if (el) {
          el.classList.add('hidden');
          el.style.display = 'none';
        }
      });
      var targetSection = document.getElementById('section-' + tabName);
      if (targetSection) {
        targetSection.classList.remove('hidden');
        targetSection.style.display = 'block';
      }
    }

    var academicDatabase = {
      "B.Tech": {
        "1": [
          { name: "Engineering Mathematics I", topics: "Linear Algebra, Calculus, Differential Equations" },
          { name: "Engineering Physics", topics: "Optics, Lasers, Quantum Theory, Fiber Optics" },
          { name: "Basic Electrical Engineering", topics: "AC Circuits, DC Network Theorems, Transformers" }
        ],
        "2": [
          { name: "Programming in C", topics: "Pointers, DMA, Structures, Recursion, File Handling" },
          { name: "Engineering Mathematics II", topics: "Fourier Series, Vector Calculus, Complex Variables" },
          { name: "Basic Electronics", topics: "Semiconductors, Diodes, BJT, Op-Amps" }
        ],
        "3": [
          { name: "Data Structures & Algorithms", topics: "Arrays, Linked Lists, Trees, Graphs, Sorting & Searching" },
          { name: "Digital Logic & Design (DLD)", topics: "Number Systems, K-Maps, Combinational & Sequential Circuits" },
          { name: "Discrete Mathematical Structures", topics: "Set Theory, Relations, Group Theory, Recurrences" }
        ],
        "4": [
          { name: "Operating Systems (OS)", topics: "Processes, CPU Scheduling, Deadlocks, Memory Management, Linux" },
          { name: "Database Management Systems (DBMS)", topics: "ER Model, Relational Algebra, SQL Queries, Normalization, ACID" },
          { name: "Computer Organization & Arch (COA)", topics: "Pipelining, Instruction Formats, Memory Hierarchy, Cache" }
        ],
        "5": [
          { name: "Design & Analysis of Algorithms (DAA)", topics: "Divide & Conquer, Dynamic Programming, Greedy, NP Completeness" },
          { name: "Computer Networks (CN)", topics: "OSI vs TCP/IP, IP Addressing, Subnetting, Routing Protocols" },
          { name: "Software Engineering", topics: "Agile Model, SDLC, SRS Documentation, Testing Techniques" }
        ],
        "6": [
          { name: "Compiler Design", topics: "Lexical Analysis, Top-Down/Bottom-Up Parsing, Code Generation" },
          { name: "Artificial Intelligence & ML", topics: "State Space Search, Heuristics, Supervised/Unsupervised ML" },
          { name: "Cloud Computing & DevOps", topics: "Virtualization, AWS Basics, Docker, Kubernetes, CI/CD" }
        ],
        "7": [
          { name: "Cybersecurity & Cryptography", topics: "Symmetric/Asymmetric Encryption, RSA, Hashing, Network Attacks" },
          { name: "Distributed Systems", topics: "RPC, MapReduce, Consensus Algorithms, Microservices" }
        ],
        "8": [
          { name: "Major Project & Viva Preparation", topics: "SRS, Architecture Diagrams, Testing Reports, Code Review" },
          { name: "System Design & Scalability", topics: "High-Level Design (HLD), Low-Level Design (LLD), Load Balancing" }
        ]
      }
    };

    function filterNotes() {
      var course = (document.getElementById('notesCourse') || {}).value || 'B.Tech';
      var branch = (document.getElementById('notesBranch') || {}).value || 'CSE';
      var sem = (document.getElementById('notesSem') || {}).value || '3';
      var container = document.getElementById('notesCardsList');
      if (!container) return;

      var courseData = academicDatabase[course] || academicDatabase["B.Tech"];
      var list = courseData[sem] || courseData["3"] || [];

      var html = '';
      list.forEach(function(item) {
        html += '<div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between space-y-4 hover:border-emerald-500/40 transition">' +
          '<div>' +
            '<div class="flex items-center justify-between">' +
              '<span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">' + course + ' ' + branch + ' • Sem ' + sem + '</span>' +
              '<span class="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">Verified</span>' +
            '</div>' +
            '<h3 class="text-base font-bold text-white mt-2">' + item.name + '</h3>' +
            '<p class="text-xs text-slate-400 mt-2 leading-relaxed"><strong>Core Topics:</strong> ' + item.topics + '</p>' +
          '</div>' +
          '<button onclick="alert(\'Downloading verified notes for ' + item.name + '...\')" class="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 flex items-center justify-center gap-2 cursor-pointer">' +
            '<span>Download Notes (PDF)</span>' +
          '</button>' +
        '</div>';
      });
      container.innerHTML = html;
    }

    var pyqData = [
      { subject: "Data Structures & Algorithms", sem: "Semester 3", year: "2024 End-Term", marks: "100 Marks" },
      { subject: "Operating Systems", sem: "Semester 4", year: "2024 Mid-Term", marks: "50 Marks" },
      { subject: "Database Management Systems", sem: "Semester 4", year: "2023 End-Term", marks: "100 Marks" },
      { subject: "Computer Networks", sem: "Semester 5", year: "2024 End-Term", marks: "100 Marks" }
    ];

    function loadPyqList() {
      var container = document.getElementById('pyqList');
      if (!container) return;
      var html = '';
      pyqData.forEach(function(p) {
        html += '<div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex items-center justify-between hover:border-emerald-500/40 transition">' +
          '<div>' +
            '<span class="text-xs font-bold text-emerald-400 uppercase">' + p.sem + '</span>' +
            '<h4 class="text-base font-bold text-white mt-0.5">' + p.subject + '</h4>' +
            '<p class="text-xs text-slate-400 mt-1">' + p.year + ' • ' + p.marks + '</p>' +
          '</div>' +
          '<button onclick="alert(\'Downloading ' + p.subject + ' ' + p.year + ' Paper...\')" class="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-500 text-slate-950 hover:bg-emerald-400 cursor-pointer">Download Paper</button>' +
        '</div>';
      });
      container.innerHTML = html;
    }

    async function askDoubtAI() {
      var query = document.getElementById('askQuery').value;
      var course = document.getElementById('askCourse').value || 'B.Tech';
      var branch = document.getElementById('askBranch').value || 'CSE';
      var subject = document.getElementById('askSubject').value || 'Computer Science';
      var btn = document.getElementById('doubtSubmitBtn');

      if (!query.trim()) { alert('Pehle apna doubt ya problem enter karein.'); return; }
      btn.disabled = true;
      btn.innerText = 'AI Assistant is solving...';

      try {
        var res = await fetch('/api/btech-doubt-solver', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query, course: course, branch: branch, semester: 'All', subject: subject })
        });
        var data = await res.json();
        document.getElementById('doubtSolutionText').textContent = data.solution;
        var box = document.getElementById('doubtSolutionBox');
        box.classList.remove('hidden');
        box.style.display = 'block';
      } catch (e) {
        alert('Error: ' + e.message);
      } finally {
        btn.disabled = false;
        btn.innerText = 'Solve with AI Assistant';
      }
    }

    var mockBank = {
      "Data Structures & Algorithms": "Explain QuickSort time complexity in Worst, Best and Average cases with partition logic.",
      "Operating Systems": "What is Deadlock? List the four Coffman conditions and explain Banker's Algorithm.",
      "Database Management Systems": "Explain differences between 3NF and BCNF with schema decomposition examples.",
      "Computer Networks": "Explain the 3-Way Handshake mechanism in TCP and describe SYN flood attacks."
    };

    function generateMockQ() {
      var sub = document.getElementById('mockSubjectPick').value;
      document.getElementById('mockQuestionText').textContent = mockBank[sub] || 'Explain core concepts in ' + sub;
      
      var area = document.getElementById('mockQuestionArea');
      area.classList.remove('hidden');
      area.style.display = 'block';

      var res = document.getElementById('mockEvaluationResult');
      res.classList.add('hidden');
      res.style.display = 'none';

      document.getElementById('mockUserAns').value = '';
    }

    async function submitMockGrading() {
      var sub = document.getElementById('mockSubjectPick').value;
      var q = document.getElementById('mockQuestionText').textContent;
      var ans = document.getElementById('mockUserAns').value;
      var btn = document.getElementById('mockGradingBtn');

      if (!ans.trim()) { alert('Pehle apna answer likhein.'); return; }
      btn.disabled = true;
      btn.innerText = 'Grading...';

      try {
        var res = await fetch('/api/evaluate-mock-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ subject: sub, question: q, user_answer: ans })
        });
        var data = await res.json();
        var out = document.getElementById('mockEvaluationResult');
        out.innerHTML = '<div class="flex justify-between items-center"><span class="font-bold text-white">Score: <strong class="text-emerald-400 text-lg">' + data.score + '/10</strong></span></div>' +
          '<p class="text-slate-300"><strong>AI Feedback:</strong> ' + data.feedback + '</p>' +
          '<p class="text-xs text-slate-400 border-t border-slate-800 pt-2"><strong class="text-emerald-400">Key Points:</strong> ' + data.ideal_points + '</p>';
        out.classList.remove('hidden');
        out.style.display = 'block';
      } catch (err) {
        alert('Grading error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerText = 'Evaluate My Answer';
      }
    }

    async function runResumeAnalysis() {
      var fileInput = document.getElementById('resumeFile');
      var jobDesc = document.getElementById('jobDescription');
      var btn = document.getElementById('careerAnalyzeBtn');

      if (!fileInput.files || fileInput.files.length === 0) { alert('PDF Resume select karein.'); return; }
      btn.disabled = true;
      btn.innerText = 'Analyzing Resume...';

      var formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('job_description', jobDesc.value);

      try {
        var res = await fetch('/api/analyze-resume', { method: 'POST', body: formData });
        var data = await res.json();
        var analysis = data.ai_analysis;

        document.getElementById('careerFilename').textContent = data.filename;
        document.getElementById('careerMatchScore').textContent = (analysis.match_percentage || 0) + '%';

        var dHtml = '';
        (analysis.candidate_skills || []).forEach(s => dHtml += '<span class="px-3 py-1 text-xs rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">' + s + '</span>');
        document.getElementById('careerDetectedSkills').innerHTML = dHtml || '<span class="text-xs text-slate-500">None detected</span>';

        var mHtml = '';
        (analysis.missing_skills || []).forEach(s => mHtml += '<span class="px-3 py-1 text-xs rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">' + s + '</span>');
        document.getElementById('careerMissingSkills').innerHTML = mHtml || '<span class="text-xs text-emerald-400">No missing skills!</span>';

        var rHtml = '';
        (analysis.learning_roadmap || []).forEach((step, i) => {
          rHtml += '<div class="flex items-start gap-2"><strong class="text-emerald-400">Step ' + (i+1) + ':</strong> <span>' + step + '</span></div>';
        });
        document.getElementById('careerRoadmap').innerHTML = rHtml;

        var cRes = document.getElementById('careerResults');
        cRes.classList.remove('hidden');
        cRes.style.display = 'block';
      } catch (err) {
        alert('Resume Error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerText = 'Analyze Resume Match with AI';
      }
    }
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def serve_home():
    return HTML_PAGE

@app.post("/api/btech-doubt-solver")
async def btech_doubt_solver(req: DoubtRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API Key Missing in backend")

    prompt = f"""
    You are an elite Computer Science Professor and B.Tech Academic Mentor.
    Course: {req.course}
    Branch: {req.branch}
    Subject: {req.subject}

    Student Query:
    {req.query}

    Provide a crystal-clear, step-by-step educational solution with code and exam points.
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
    Candidate Answer: {req.user_answer}

    Grade this answer out of 10 for university standard.
    Return ONLY a valid JSON object:
    {{
        "score": 8,
        "feedback": "2 concise sentences on technical accuracy and missing concepts",
        "ideal_points": "Key definitions, logic or diagrams required for full marks"
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
    Resume Content: {extracted_text}
    Job Description: {job_description}

    Evaluate match strictly and return ONLY a valid JSON object:
    {{
        "candidate_skills": ["detected skills"],
        "missing_skills": ["missing skills"],
        "match_percentage": 78,
        "learning_roadmap": [
            "Week 1: Foundations",
            "Week 2: Advanced projects"
        ]
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return {"filename": file.filename, "ai_analysis": json.loads(response.text)}