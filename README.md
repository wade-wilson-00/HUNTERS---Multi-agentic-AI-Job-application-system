<div align="center">

# 🏹 H U N T E R S

### *Your AI-Powered Career Operating System*

<br>

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Framework-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Meta Llama](https://img.shields.io/badge/Meta_Llama_3.1-8B_Instruct-0467DF?style=for-the-badge&logo=meta&logoColor=white)](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Inference_API-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Memory-FF6F61?style=for-the-badge&logo=databricks&logoColor=white)](https://www.trychroma.com)
[![Rich](https://img.shields.io/badge/Rich-CLI_UI-4B0082?style=for-the-badge&logo=gnometerminal&logoColor=white)](https://github.com/Textualize/rich)

<br>

*A voice-enabled, multi-agent AI system that listens to you, understands your career goals, and autonomously hunts for job opportunities — like having J.A.R.V.I.S. as your personal career advisor.*

<br>

---

</div>

## 🎯 What is HUNTERS?

**HUNTERS** is an advanced multi-agentic AI career operating system — not a chatbot, not a wrapper, but a fully autonomous pipeline of specialized AI agents that **hunt jobs for you**.

You don't scroll job boards. You don't write cover letters. You don't track applications in spreadsheets. You just **talk**.

Think of it as **J.A.R.V.I.S. meets an entire recruitment agency**, except it works 24/7, never forgets your preferences, and actually submits applications on your behalf.

**The Vision:**
> *"Hunter, find AI Engineering internships in Bangalore, rank them against my profile, draft cover letters for the top 3, and apply to all of them."*

Hunter will listen, understand your intent, delegate tasks across a network of specialized AI agents — Scout, Resume Analyzer, Match, Apply, Outreach, Tracker — orchestrate their work through LangGraph, use MCP tools to interact with real-world systems (browsers, file systems, Notion, Gmail), generate evidence reports, ask for your approval on critical actions, and speak the results back to you. **End-to-end. Fully automated.**

---

## 🧠 How It Works

```
     🎙 You Speak
          │
          ▼
   ┌──────────────┐
   │   Listener    │  ← Captures microphone input
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Transcriber  │  ← Converts speech to text (Google STT)
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Hunter LLM   │  ← Meta Llama 3.1 via HuggingFace
   │  (The Brain)  │     Processes intent, generates response
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   TTS Engine  │  ← Speaks the response aloud (Male voice)
   └──────┬───────┘
          │
          ▼
     🗣 You Hear Hunter's Response
```

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center" width="120">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48" height="48" alt="Python" />
<br><strong>Python</strong>
<br><sub>3.12+</sub>
</td>
<td align="center" width="120">
<img src="https://huggingface.co/front/assets/huggingface_logo-noborder.svg" width="48" height="48" alt="HuggingFace" />
<br><strong>HuggingFace</strong>
<br><sub>Inference API</sub>
</td>
<td align="center" width="120">
<img src="https://avatars.githubusercontent.com/u/126733545?s=48&v=4" width="48" height="48" alt="LangGraph" />
<br><strong>LangGraph</strong>
<br><sub>Agent Orchestration</sub>
</td>
<td align="center" width="120">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg" width="48" height="48" alt="SQLite" />
<br><strong>ChromaDB</strong>
<br><sub>Vector Memory</sub>
</td>
</tr>
<tr>
<td align="center" width="120">
<br>🦙
<br><strong>Llama 3.1</strong>
<br><sub>8B Instruct</sub>
</td>
<td align="center" width="120">
<br>🎙️
<br><strong>Whisper / STT</strong>
<br><sub>Speech-to-Text</sub>
</td>
<td align="center" width="120">
<br>🗣️
<br><strong>pyttsx3</strong>
<br><sub>Text-to-Speech</sub>
</td>
<td align="center" width="120">
<br>💻
<br><strong>Typer + Rich</strong>
<br><sub>CLI Interface</sub>
</td>
</tr>
</table>

---

## 📦 Project Structure

```
hunters/
├── app.py                  # Main CLI entry point (Voice Loop)
│
├── agents/
│   ├── llm.py              # HuggingFace InferenceClient setup
│   ├── hunter.py           # Hunter Agent (Jarvis-style supervisor)
│   ├── scout.py            # 🔜 Job search & opportunity discovery
│   ├── resume_analyzer.py  # 🔜 Resume parsing & strength analysis
│   ├── match.py            # 🔜 Job-resume matching & ranking
│   ├── apply.py            # 🔜 Automated job application agent
│   ├── outreach.py         # 🔜 Recruiter outreach & cold emails
│   ├── tracker.py          # 🔜 Application status tracking
│   └── researcher.py       # 🔜 AI trends & market research
│
├── voice/
│   ├── listener.py         # Microphone capture & audio recording
│   ├── whisper_engine.py   # Speech-to-Text transcription
│   └── tts.py              # Text-to-Speech engine (Male voice)
│
├── graph/                  # 🔜 LangGraph workflow definitions
├── memory/                 # 🔜 ChromaDB vector stores
├── tools/                  # 🔜 MCP tool integrations
├── mcp_servers/            # 🔜 MCP server configs (Browser, FS, Notion, Gmail)
├── prompts/                # 🔜 Agent system prompts library
├── templates/              # 🔜 Resume/cover letter generation templates
├── reports/                # 🔜 Agent-generated evidence reports
├── workspace/              # 🔜 Working directory for agents
├── tests/                  # 🔜 Unit & integration tests
│
├── requirements.txt
├── roadmap.md
├── system_architecure.md
└── .env                    # API keys (not committed)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- A microphone
- A [HuggingFace API Key](https://huggingface.co/settings/tokens) with access to Meta Llama 3.1

### Installation

```bash
# Clone the repository
git clone https://github.com/wade-wilson-00/HUNTERS---Multi-agentic-AI-Job-application-system.git
cd HUNTERS---Multi-agentic-AI-Job-application-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
# Create a .env file with:
HUGGING_FACE_API=your_huggingface_api_key_here
```

### Run Hunter

```bash
python app.py
```

Press **Enter**, speak your question, and Hunter will respond with a voice!

---

## 📋 Development Progress

### ✅ Week 1 — Hunter Core (Voice Assistant) `COMPLETED`

The foundational voice-to-voice loop is fully operational.

| Feature | Status | Description |
|---------|--------|-------------|
| Microphone Listener | ✅ Done | Captures voice input with ambient noise calibration |
| Speech-to-Text | ✅ Done | Transcribes audio using Google Speech Recognition |
| LLM Brain | ✅ Done | Meta Llama 3.1 (8B) via HuggingFace Inference API |
| Text-to-Speech | ✅ Done | Male voice (Microsoft David) via pyttsx3 |
| CLI Interface | ✅ Done | Beautiful terminal UI with Rich panels & Typer |
| Voice Loop | ✅ Done | Continuous listen → think → speak cycle |
| Jarvis Persona | ✅ Done | Witty, polite, British-style AI assistant personality |

---

### 🔨 Week 2 — Hunter Supervisor + LangGraph `IN PROGRESS`

Turning Hunter from a chatbot into a planner with intent detection and task delegation.

| Feature | Status | Description |
|---------|--------|-------------|
| LangGraph Integration | 🔜 Pending | Nodes, edges, state management, routing |
| HunterState | 🔜 Pending | Shared state object (goals, tasks, reports) |
| Intent Detection | 🔜 Pending | Parse natural language into structured intents |
| Planning Layer | 🔜 Pending | Generate multi-step task plans from goals |
| First LangGraph Workflow | 🔜 Pending | Hunter → Planner → Summary pipeline |

---

### 📌 Week 3 — Multi-Agent System `UPCOMING`

Creating specialized agents that Hunter delegates tasks to.

| Feature | Status | Description |
|---------|--------|-------------|
| Scout Agent | 🔜 Pending | Search and gather job opportunities |
| Resume Agent | 🔜 Pending | Analyze user profile and career strengths |
| Match Agent | 🔜 Pending | Compare and rank jobs against resume |
| ChromaDB Memory | 🔜 Pending | Persistent vector storage for profile data |
| Agent Reports | 🔜 Pending | Each agent generates evidence documents |

---

### 📌 Week 4 — MCP + Real-World Tools `UPCOMING`

Connecting agents to real-world systems via Model Context Protocol.

| Feature | Status | Description |
|---------|--------|-------------|
| Filesystem MCP | 🔜 Pending | Read/write files, save reports |
| Browser MCP | 🔜 Pending | Web scraping, job board access |
| Notion MCP | 🔜 Pending | Application tracking dashboard |
| Tracker Agent | 🔜 Pending | Maintain application records |
| Human Approval Layer | 🔜 Pending | User confirms before critical actions |

---

### 📌 Week 5 — Apply Agent + Outreach Agent `UPCOMING`

Automating the actual job application process end-to-end.

| Feature | Status | Description |
|---------|--------|-------------|
| Apply Agent | 🔜 Pending | Browser automation for one-click job applications |
| Resume Tailoring | 🔜 Pending | Auto-customize resume per job description |
| Cover Letter Generation | 🔜 Pending | Generate tailored cover letters using templates |
| Outreach Agent | 🔜 Pending | Draft and send recruiter cold emails via Gmail MCP |
| Gmail MCP | 🔜 Pending | Email integration for outreach automation |
| Application Pipeline | 🔜 Pending | Scout → Match → Apply → Track in one command |

---

### 📌 Week 6 — Autonomous Mode + Polish `UPCOMING`

Making Hunter a fully autonomous, always-ready career companion.

| Feature | Status | Description |
|---------|--------|-------------|
| Wake Word | 🔜 Pending | "Hey Hunter" always-on voice activation |
| Daily Briefings | 🔜 Pending | Automated morning career opportunity reports |
| Autonomous Hunts | 🔜 Pending | Hunter runs overnight job searches autonomously |
| Scheduled Scans | 🔜 Pending | Cron-based periodic job market scanning |
| Career Dashboard | 🔜 Pending | Rich CLI dashboard with stats & analytics |
| Full Pipeline Test | 🔜 Pending | End-to-end voice → apply → track integration |

---

## 🔮 Future Vision

Once the core 6-week system is battle-tested, the long-term vision includes:

- **Interview Prep Agent** — Mock interviews with real-time feedback and scoring
- **Salary Negotiation Agent** — Market research and negotiation strategy generation
- **Network Agent** — LinkedIn connection automation and relationship tracking
- **Portfolio Agent** — Auto-generate project showcases from GitHub repos
- **Multi-Platform Support** — Extend beyond CLI to mobile app and web dashboard
- **Team Mode** — Multiple users sharing a single Hunter instance for group job hunts

---

## 🏗️ System Architecture

```
                     🎙 User Voice
                           │
                           ▼
                   Speech-to-Text
                    (Whisper/STT)
                           │
                           ▼
                 HUNTER SUPERVISOR
                      LangGraph
                           │
       ┌──────────┬────────┴──────┬──────────┐
       │          │               │          │
       ▼          ▼               ▼          ▼
    Scout      Resume          Match     Tracker
    Agent      Agent           Agent      Agent
       │          │               │          │
       ▼          ▼               ▼          ▼
    Apply     Outreach        Memory     Notion
    Agent      Agent          Agent      Agent
                           │
                           ▼
                    Shared State
                           │
                           ▼
                   Hunter Summary
                           │
                           ▼
                    Text-to-Speech
                         (TTS)
                           │
                           ▼
                       🗣 User
```

---

## 🤝 Contributing

This project is currently in active development as a personal AI engineering learning project. Contributions, ideas, and feedback are welcome!

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built with 🤍 and a dream of never manually applying to jobs again.**

*"Good evening, sir. Shall I begin the hunt?"* — Hunter 🏹

</div>
