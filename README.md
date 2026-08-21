<div align="center">

```text
██   ██  ██   ██  ███   ██  ████████  ███████   ██████    ███████ 
██   ██  ██   ██  ████  ██     ██     ██        ██   ██   ██      
███████  ██   ██  ██ ██ ██     ██     █████     ██████    ███████ 
██   ██  ██   ██  ██  ████     ██     ██        ██   ██        ██ 
██   ██  ███████  ██   ███     ██     ███████   ██   ██   ███████ 
```

### *Your AI-Powered Career Operating System*

<br>

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSockets-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq-Inference-f55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Qwen](https://img.shields.io/badge/Qwen-3.6_27B_Planner-6B21A8?style=for-the-badge&logo=alibabadotcom&logoColor=white)](https://huggingface.co/Qwen)
[![Gemini](https://img.shields.io/badge/Gemini-3.6_Flash_Memory-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Cohere](https://img.shields.io/badge/Cohere-Neural_Reranker-D97706?style=for-the-badge)](https://cohere.com)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-STT-FF9900?style=for-the-badge)](https://www.sarvam.ai/)
[![Rich](https://img.shields.io/badge/Rich-CLI_UI-4B0082?style=for-the-badge&logo=gnometerminal&logoColor=white)](https://github.com/Textualize/rich)
[![FastMCP](https://img.shields.io/badge/FastMCP-Tooling-blue?style=for-the-badge)](https://github.com/jlowin/fastmcp)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Loop-green?style=for-the-badge)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Memory-E85D04?style=for-the-badge)](https://www.trychroma.com/)
[![BGE](https://img.shields.io/badge/BGE--small--en-Embeddings-6929C4?style=for-the-badge)](https://huggingface.co/BAAI/bge-small-en-v1.5)
[![SQLite](https://img.shields.io/badge/SQLite-State_Persistence-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

<br>

*A hyper-optimized, voice-enabled AI system that listens to you, understands your career goals, and autonomously hunts for job opportunities — like having J.A.R.V.I.S. as your personal career advisor.*

<br>

---

</div>

## 🎯 What is HUNTERS?

**HUNTERS** is an advanced multi-agentic AI career operating system — not a chatbot, not a wrapper, but a fully autonomous pipeline of specialized AI agents that **hunt jobs for you**.

You don't scroll job boards. You don't write cover letters. You don't track applications in spreadsheets. You just **talk**.

Think of it as **J.A.R.V.I.S. meets an elite recruitment agency**, except it works 24/7, never forgets your preferences, and actually submits applications on your behalf.

**The Vision:**
> *"Hunter, find AI Engineering internships in Bangalore, rank them against my profile, draft cover letters for the top 3, and apply to all of them."*

Hunter will listen, understand your intent, delegate tasks across a network of specialized AI agents — Scout, Resume Analyzer, Match, Apply, Outreach, Tracker — orchestrate their work through LangGraph, use MCP tools to interact with real-world systems (browsers, file systems, Notion, Gmail), and speak the results back to you in **real-time**. End-to-end. Fully automated.

---

## ⚡ Real-Time Voice Architecture (New!)

We recently rebuilt Hunter's voice pipeline from the ground up into a highly scalable asynchronous Client-Server architecture to achieve **zero-latency, conversational AI interactions**.

```text
      🎙 You Speak (Voice Mode) / ⌨️ You Type (Text Mode)
            │
            ▼
     ┌──────────────┐
     │ VAD Listener │  ← Silero VAD detects voice & locks out noise
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │  FastAPI WS  │  ← Streams audio bytes over WebSockets
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │  Sarvam STT  │  ← Ultra-fast Speech-to-Text inference
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │ Hunter Graph │  ← LangGraph ReAct Loop (Planner ↔ Tools)
     │ (ChatGroq)   │  ← FastMCP tools: read_resume, search_web
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │Local Edge TTS│  ← Client chunks text & runs neural TTS locally for zero lag
     └──────┬───────┘
            │
            ▼
       🗣 You Hear Hunter (Real-time concurrent playback!)
```

### 🔥 Key Optimizations & Fixes
- **Client-Side Edge TTS:** TTS generation was moved from the server directly to the client. This cuts out an entire network hop, meaning Hunter starts speaking the very millisecond the first sentence is generated!
- **Asynchronous Concurrent Playback:** Utilizing pure `asyncio` and `miniaudio`, the audio stream buffers and plays chunks concurrently as they download, preventing deadlocks and buffering lag.
- **Groq LLM Acceleration:** Switched to Groq's high-speed inference for Llama 3.1, making the AI's "thought process" nearly instantaneous.
- **VAD Processing Lock:** The microphone now intelligently mutes itself (`is_processing`) while Hunter is processing and speaking, eliminating the dreaded "one-word mid-sentence reset" bug.
- **3D Pixel UI:** Built a gorgeous custom 3D drop-shadow CLI interface natively into Rich, replacing standard fonts.

---

## 🧠 Hunter's LangGraph Architecture

Hunter's brain is a **ReAct (Reason + Act)** Agent built on LangGraph — capable of autonomously reasoning, calling tools, and maintaining memory across restarts.

```mermaid
graph TD
    User(["User Input"]) --> Planner

    subgraph HunterGraph ["LangGraph HunterState"]
        Planner["Planner Node\nQwen 3.6 27B\nReAct Reasoning"] -- Tool Call --> ToolNode
        ToolNode["Tool Execution Node"] -- Result --> Planner
        Planner -- Response Ready --> Summary
        Summary["Summary Node\nVoice Post-Processor"]
    end

    subgraph MCPServer ["Central FastMCP Server"]
        read_resume["read_resume"]
        search_web["search_web"]
        search_past_memories["search_past_memories"]
    end

    subgraph MemoryWrite ["Write Path — After Every Turn"]
        direction TB
        EpisodicMerge["Phase 1: Episodic Merge\nGemini 3.6 Flash\nSingle-doc LLM Upsert"]
        SemanticExtract["Phase 2: Semantic Extraction\nGemini 3.6 Flash JSON Mode\nFact Diff + Conflict Resolution"]
        ChromaDB[("ChromaDB\nLong-Term Memory")]
        EpisodicMerge --> ChromaDB
        SemanticExtract --> ChromaDB
    end

    subgraph MemoryRead ["Read Path — On Demand"]
        direction TB
        BM25["BM25 Sparse Search"]
        Dense["BGE-small Dense Search"]
        RRF["RRF Fusion\ntop-15 pool"]
        Cohere["Phase 3: Cohere Rerank\nrerank-english-v3.0\nNeural Cross-Encoder"]
        BM25 --> RRF
        Dense --> RRF
        RRF --> Cohere
    end

    subgraph ShortTerm ["Short-Term State"]
        SQLite[("SQLite\nCheckpoint Store")]
    end

    ToolNode -. stdio .-> read_resume
    ToolNode -. stdio .-> search_web
    ToolNode -. stdio .-> search_past_memories

    Summary --> EpisodicMerge
    Summary --> SemanticExtract
    Summary -- Checkpoint --> SQLite
    search_past_memories --> BM25
    search_past_memories --> Dense
    Dense -. BGE Embed .-> ChromaDB
    ChromaDB -. fetch docs .-> BM25
    Cohere -- Top-N Results --> Planner
    SQLite -. Reload on Restart .-> Planner
    Summary --> Out(["Voice Output"])

    classDef llm fill:#f55036,stroke:#fff,stroke-width:2px,color:#fff
    classDef node fill:#009688,stroke:#fff,stroke-width:2px,color:#fff
    classDef mcp fill:#3776AB,stroke:#fff,stroke-width:2px,color:#fff
    classDef mem fill:#6929C4,stroke:#fff,stroke-width:2px,color:#fff
    classDef gemini fill:#4285F4,stroke:#fff,stroke-width:2px,color:#fff
    classDef cohere fill:#D97706,stroke:#fff,stroke-width:2px,color:#fff
    classDef fusion fill:#166534,stroke:#fff,stroke-width:2px,color:#fff

    class Planner,Summary llm
    class ToolNode node
    class read_resume,search_web,search_past_memories mcp
    class ChromaDB,SQLite mem
    class EpisodicMerge,SemanticExtract gemini
    class Cohere cohere
    class RRF fusion
```

### 🧠 Dual Memory — How It Works

Hunter has two independent memory systems working in parallel:

| Memory Layer | Technology | Purpose |
|---|---|---|
| **Short-Term (State)** | SQLite + `AsyncSqliteSaver` | Persists the full LangGraph message state across restarts. Restart `app.py` and Hunter picks up right where it left off. |
| **Long-Term (Episodic)** | ChromaDB + Gemini 3.6 Flash | After every session, Gemini intelligently merges new conversation content into a single evolving episodic document — no bloat, no duplicates. |
| **Long-Term (Semantic)** | ChromaDB + Gemini 3.6 Flash JSON Mode | Gemini extracts structured atomic facts (skills, goals, location, preferences) per turn. Stale/contradicted facts are automatically deleted and replaced. |

---

## 🔍 Hybrid Storing & Retrieval — RAG for Your Career Data

Hunter's long-term memory uses a **production-grade two-stage RAG pipeline** that ensures you always get the most accurate and relevant information recalled — not just the most recent or most verbatim-matched.

### ✍️ Write Path — Smart Memory Storage (After Every Turn)

Every session is processed by two parallel Gemini-powered pipelines:

```
summary_node
  ├── Phase 1: add_episodic_memory()
  │     └── Gemini 3.6 Flash reads existing episode + new session
  │           → Merges into one coherent narrative document (upsert)
  │           → ChromaDB always holds exactly ONE episodic doc
  │
  └── Phase 2: add_semantic_memory()
        └── Gemini 3.6 Flash (JSON mode) reads existing facts + new turn
              → Extracts: skill | target_role | location | preference | constraint | experience
              → Deletes superseded/contradicted facts automatically
              → Writes only genuinely new facts to ChromaDB
```

**Why this matters for you:** Hunter never stores stale data. If you say *"I've moved to Dubai"*, Gemini automatically removes your old Karachi location fact and stores the new one — no manual correction needed.

### 🔎 Read Path — Two-Stage Retrieval (On Demand)

When the Planner needs past context (via the `search_past_memories` MCP tool), it runs a two-stage retrieval pipeline:

```
Query: "What are my Python skills and job preferences?"
  │
  ├── Stage 1: Recall (wide net)
  │     ├── A. Dense Search  — BGE-small-en embeddings via ChromaDB (semantic similarity)
  │     ├── B. Sparse Search — BM25Okapi keyword matching (exact terms, tech names, dates)
  │     └── C. RRF Fusion   — Reciprocal Rank Fusion combines both, pools top 15 candidates
  │
  └── Stage 2: Precision (neural cross-encoder)
        └── Cohere rerank-english-v3.0 API
              → Scores all 15 (query, document) pairs using a cross-encoder
              → Returns top 4 by absolute relevance score
              → Gracefully falls back to RRF if API unavailable
```

| Retrieval Dimension | Technology | What it catches |
|---|---|---|
| **Semantic Similarity** | BGE-small-en (dense vectors) | "job preferences" ↔ "career goals", conceptual matches |
| **Keyword Matching** | BM25Okapi (sparse TF-IDF) | Exact tech names, dates, company names, numbers |
| **Score Fusion** | Reciprocal Rank Fusion (k=60) | Best of both worlds — no single retriever blind spots |
| **Neural Reranking** | Cohere `rerank-english-v3.0` | Understands full query intent, not just token overlap |

**The result:** When you ask Hunter *"What job applications did I have in progress?"*, it doesn't just do a keyword search — it understands your intent, retrieves the 15 most plausible memories, then Cohere's cross-encoder picks the 4 that are *actually* relevant to that specific question.

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
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="48" height="48" alt="FastAPI" />
<br><strong>FastAPI</strong>
<br><sub>WS Server</sub>
</td>
<td align="center" width="120">
<img src="brand_logos/langgraph.png" width="48" height="48" alt="LangGraph" />
<br><strong>LangGraph</strong>
<br><sub>Agent Orchestration</sub>
</td>
<td align="center" width="120">
<img src="brand_logos/Model_Context_Protocol_logo-removebg-preview.png" width="48" height="48" alt="MCP" />
<br><strong>FastMCP</strong>
<br><sub>Stdio Tool Server</sub>
</td>
</tr>
<tr>
<td align="center" width="120">
<img src="https://qianwen-res.oss-cn-beijing.aliyuncs.com/logo/qwen.png" width="48" height="48" alt="Qwen" onerror="this.src='https://img.shields.io/badge/Qwen-27B-6B21A8?style=flat-square'" />
<br><strong>Qwen</strong>
<br><sub>3.6 27B Planner LLM</sub>
</td>
<td align="center" width="120">
<img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" width="48" height="48" alt="Gemini" />
<br><strong>Gemini</strong>
<br><sub>3.6 Flash Memory AI</sub>
</td>
<td align="center" width="120">
<img src="https://asset.brandfetch.io/idHMCKxoEf/idawOgEAPN.svg" width="48" height="48" alt="Cohere" />
<br><strong>Cohere</strong>
<br><sub>Neural Reranker</sub>
</td>
<td align="center" width="120">
<img src="brand_logos/groq.png" width="48" height="48" alt="Groq" />
<br><strong>Groq</strong>
<br><sub>LLM Inference</sub>
</td>
</tr>
<tr>
<td align="center" width="120">
<img src="brand_logos/sarvam-removebg-preview.png" width="48" height="48" alt="Sarvam AI" />
<br><strong>Sarvam AI</strong>
<br><sub>Ultra-fast STT</sub>
</td>
<td align="center" width="120">
<img src="brand_logos/edge-removebg-preview.png" width="48" height="48" alt="Microsoft Edge" />
<br><strong>Edge TTS</strong>
<br><sub>Streaming Neural TTS</sub>
</td>
<td align="center" width="120">
<img src="brand_logos/richlogo_py_wide_featured-removebg-preview.png" width="90" height="48" alt="Rich" />
<br><strong>Rich</strong>
<br><sub>CLI UI</sub>
</td>
<td align="center" width="120">
<img src="https://huggingface.co/front/assets/huggingface_logo-noborder.svg" width="48" height="48" alt="BAAI BGE" />
<br><strong>BGE-small-en</strong>
<br><sub>384-dim Embeddings</sub>
</td>
</tr>
</table>

---

## 📦 Project Structure

```
hunters/
├── app.py                        # CLI entry point — Voice/Text mode selector
│
├── agents/
│   ├── hunter.py                 # HunterAgent — orchestrates the LangGraph run
│   └── graphs/
│       ├── hunter_graph.py       # Graph builder — MCP client, nodes, edges
│       ├── hunter_state.py       # HunterState TypedDict (messages, intent, response)
│       ├── planner.py            # Planner node — ReAct reasoning, tool binding
│       ├── summary.py            # Summary node — voice post-processor + memory indexing
│       └── groq_llm.py           # Shared ChatGroq LLM instance
│
├── context/
│   ├── context_builder.py        # Lean system prompt builder (5-layer, tool-first)
│   └── memory_store.py           # ChromaDB + BGE-small-en embeddings (long-term memory)
│
├── mcp_server/
│   ├── central_server.py         # FastMCP stdio server — registers all tools
│   └── tools/
│       ├── resume_read.py        # read_resume — reads workspace_profile/ files
│       ├── web_search.py         # search_web — Tavily live internet search
│       └── memory_tool.py        # search_past_memories — Chroma semantic search
│
├── server/
│   ├── voice_server.py           # FastAPI WebSocket server (Voice Mode)
│   └── sarvam_stt.py             # Sarvam AI STT client
│
├── voice/
│   ├── vad_listener.py           # Silero VAD continuous voice detection
│   ├── stream_tts.py             # Sentence chunker & Edge TTS streaming
│   └── audio_stream.py           # Async miniaudio concurrent playback
│
├── workspace_profile/            # Drop your resume/portfolio here (not committed)
│   └── resume.md
│
├── .data/                        # Runtime data (not committed)
│   ├── hunter_state.db           # SQLite — short-term state persistence
│   └── chroma_db/                # ChromaDB — long-term semantic memory
│
├── config/
│   └── settings.py               # App-wide constants (model IDs, paths, URLs)
│
├── sub_agents/                   # 🔜 Scout, Match, Apply, Outreach agents
├── prompts/                      # 🔜 Agent system prompts library
├── templates/                    # 🔜 Cover letter & resume templates
├── tests/                        # 🔜 Unit & integration tests
│
├── requirements.txt
└── .env                          # API keys (never committed)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- A microphone
- Groq API Key
- Sarvam AI API Key

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
GROQ_API_KEY=your_groq_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
```

### Run Hunter

```bash
# 1. Start the Voice WebSocket Server
python -m server.voice_server

# 2. Start the Client (in a new terminal)
python app.py
```

The app supports two modes:
- **Voice Mode**: Speak naturally. Hunter uses Silero VAD to know when you've stopped speaking and replies automatically.
- **Text Mode**: Use standard keyboard input if you prefer not to talk, while still getting voice responses.

---

## 📋 Development Progress

### ✅ Week 1 — Hunter Core (Voice Assistant) `COMPLETED`

The foundational voice-to-voice loop is fully operational.

| Feature | Status | Description |
|---------|--------|-------------|
| Voice Server | ✅ Done | FastAPI WebSocket server handling bi-directional audio/text streaming |
| Microphone Listener | ✅ Done | Fast voice activity detection using **Silero VAD** |
| Speech-to-Text | ✅ Done | Rapid cloud transcription using **Sarvam AI** |
| LLM Brain | ✅ Done | Meta Llama 3.1 (8B) via **Groq** with SSE streaming |
| Text-to-Speech | ✅ Done | Ultra-realistic, fast, streaming neural voice using **Edge TTS** |
| CLI Interface | ✅ Done | Beautiful dual-mode (Voice/Text) terminal UI with a **Custom 3D Pixel UI** |
| Zero-Latency Playback | ✅ Done | Client-side TTS with `asyncio` queueing for concurrent downloading & speaking |

---

### ✅ Week 2 — Hunter Supervisor + LangGraph `COMPLETED`

Turning Hunter from a chatbot into a dynamic ReAct planner with intent detection and tool delegation.

| Feature | Status | Description |
|---------|--------|-------------|
| FastMCP Server | ✅ Done | Centralized stdio server exposing filesystem and web tools. |
| Tool 1: read_resume | ✅ Done | Reads user profiles/resumes from PDF, DOCX, and MD files. |
| Tool 2: search_web | ✅ Done | Uses Tavily API to fetch live internet results and news. |
| LangGraph Core | ✅ Done | Replaced raw LLM streaming with a full `StateGraph` workflow. |
| HunterState | ✅ Done | TypedDict memory tracking message history and final responses. |
| Planner Node | ✅ Done | `ChatGroq` bound to MCP tools, handling reasoning and task planning. |
| Summary Node | ✅ Done | Post-processing node to translate raw markdown/data into conversational speech. |

---

### ✅ Week 3 — Dual Memory System + Context Refactor `COMPLETED`

Gave Hunter a persistent brain — short-term state that survives restarts and long-term semantic recall across conversations.

| Feature | Status | Description |
|---------|--------|-------------|
| Short-Term Memory | ✅ Done | `AsyncSqliteSaver` checkpoints the full LangGraph state to `.data/hunter_state.db` on every turn. Restart `app.py` and Hunter resumes the same thread seamlessly. |
| Long-Term Memory | ✅ Done | Every completed turn is embedded with `BAAI/bge-small-en-v1.5` (via `fastembed`) and stored in a persistent **ChromaDB** vector database at `.data/chroma_db/`. |
| `search_past_memories` Tool | ✅ Done | New MCP tool performs cosine-similarity semantic search over all past turns, letting Hunter recall preferences, prior searches, and context from any previous session. |
| Auto-Indexing | ✅ Done | `summary_node` automatically indexes every turn after generating the voice response — zero manual steps required. |
| Lean Context Builder | ✅ Done | Rewrote `context_builder.py` into a 5-layer, tool-first system prompt (~2k tokens). Raw resume content is no longer dumped into every request — Hunter calls `read_resume` on demand instead. |
| Token Window Guard | ✅ Done | Planner node caps message history at the last 6 turns and truncates tool outputs beyond 1,500 chars, keeping requests comfortably under Groq's 6,000 TPM rate limit. |
| Shared MCP Client | ✅ Done | Graph builder fetches tools once from a single MCP subprocess. `ToolNode` and `make_planner_node()` share the same list — no duplicate process spawns per turn. |

---

### ✅ Week 4 — Memory Architecture Overhaul + Stability Fixes `COMPLETED`

Hardened Hunter's entire memory system against token rate limits, infinite tool loops, database bloat, and retrieval blind spots — while laying the groundwork for multi-agent data pipelines.

#### 🧠 Short-Term Memory (STM) Improvements

| Feature | Status | Description |
|---------|--------|-------------|
| `AnyMessage` Schema Upgrade | ✅ Done | Switched `HunterState.messages` from abstract `BaseMessage` to `AnyMessage` (discriminated union). Enables accurate Pydantic deserialization from SQLite and clean static type checking for `.tool_calls`, `.tool_call_id`, etc. |
| Explicit State Variables | ✅ Done | Added structured optional fields `target_role`, `preferred_role`, `active_company`, and `summary` to `HunterState`. Key domain facts are now first-class state citizens instead of buried in raw message history. |
| Targeted Tool Truncation | ✅ Done | Planner node truncation now targets **only `ToolMessage` instances** via `is_tool` type check. `HumanMessage` and `AIMessage` pass through completely intact — preventing mid-sentence cuts on long user prompts or AI responses. |
| List-Type Truncation Fix | ✅ Done | Updated truncation to normalize `list`-type tool content (MCP stdio returns structured content blocks). Any ChromaDB or web search result returned as a list of dicts is now correctly flattened and clipped at 800 chars. |
| `RemoveMessage` State Pruning | ✅ Done | Integrated LangGraph's `RemoveMessage` sentinel into `summary_node`. When `len(messages) > 6`, old turns are permanently purged from SQLite using targeted `DELETE` operations, keeping the DB lean forever. |
| Recursion Limit Circuit Breaker | ✅ Done | Added `recursion_limit: 6` to the LangGraph graph invocation config, capping the tool-call cycle at 3 tools per turn. Prevents infinite `search_past_memories` loops from cascading into 429 rate limit errors. |
| Single LLM Instance | ✅ Done | Consolidated `planner_llm` and `summary_llm` into a single `hunter_llm` instance with `max_tokens=600`. Halved per-turn Groq API calls from 2 → 1, dropping TPM consumption from ~3,500 to ~2,100 tokens per turn. |
| Resume State Caching | ✅ Done | `cached_resume` is stored in `HunterState` after the first `read_resume` call. The planner injects it directly into the system prompt on all future turns — the tool is never called again for the same session. |

#### 🗃️ Long-Term Memory — Phase 1: Smart Episodic Merge

| Feature | Status | Description |
|---------|--------|-------------|
| LLM-Powered Episodic Upsert | ✅ Done | `add_episodic_memory()` refactored with a Gemini 3.6 Flash merge strategy. Checks ChromaDB for an existing episode; if found, sends both old + new session to Gemini which produces a single merged, coherent summary. The old doc is deleted and the merged version is upserted. Result: exactly **one** episodic document in ChromaDB at all times — no bloat. |
| Zero Information Loss | ✅ Done | New session details are woven into the existing narrative rather than appended as a new document. No context is ever dropped between sessions. |
| `summary_node` Integration | ✅ Done | `add_episodic_memory()` is called automatically after every completed turn — zero manual steps. |

#### 🧬 Long-Term Memory — Phase 2: Semantic Fact Extraction

| Feature | Status | Description |
|---------|--------|-------------|
| Gemini JSON-Mode Extraction | ✅ Done | `add_semantic_memory()` refactored to call Gemini 3.6 Flash in strict JSON mode (`temperature=0.1`). Gemini sees all existing facts + new conversation turn and returns `{"add_facts": [...], "remove_ids": [...]}`. |
| Automatic Conflict Resolution | ✅ Done | If a user updates their location, salary expectation, or role preference, Gemini automatically identifies the stale fact by ID and schedules it for deletion before writing the new one. Zero stale data. |
| Structured Fact Categories | ✅ Done | Facts are stored with typed `category` metadata: `skill`, `target_role`, `location`, `preference`, `constraint`, `experience` — enabling precision category-scoped retrieval. |
| `summary_node` Integration | ✅ Done | `add_semantic_memory()` runs in parallel with episodic indexing after every turn — both write paths fire automatically. |

#### 🎯 Long-Term Memory — Phase 3: Cohere Neural Reranking

| Feature | Status | Description |
|---------|--------|-------------|
| Two-Stage `hybrid_search()` | ✅ Done | Refactored `hybrid_search()` to add Stage 2 Cohere reranking inline. Stage 1 (Dense + BM25 + RRF) pools top 15 candidates; Stage 2 sends them all to Cohere's `rerank-english-v3.0` cross-encoder for neural scoring. Returns top `n_results` by absolute relevance score. |
| Cohere `rerank-english-v3.0` | ✅ Done | Uses Cohere's production neural reranking API — a cross-encoder that scores each (query, document) pair holistically, far beyond lexical or cosine similarity. |
| BM25 Sparse Search | ✅ Done | `rank-bm25` (`BM25Okapi`) catches exact keyword matches (tech names, company names, dates) that dense vector search misses. |
| Dense Vector Search | ✅ Done | `BAAI/bge-small-en-v1.5` (384-dim) handles conceptual/semantic similarity — *"career goals"* matching *"job preferences"*. |
| RRF Fusion | ✅ Done | Reciprocal Rank Fusion (`k=60`) merges dense + sparse rankings into a unified top-15 recall pool before reranking. |
| Graceful Fallback | ✅ Done | If `COHERE_API_KEY` is absent or the API call fails, `hybrid_search()` silently falls back to pure RRF ranking — no crash, no interruption. |
| `search_past_memories` Tool | ✅ Done | MCP tool routes through the full two-stage pipeline. Supports optional `memory_type` filter to scope results to `"semantic"` or `"episodic"` partitions. |

---

### 📌 Upcoming

| Week | Goal | Description |
|------|------|-------------|
| **Week 5** | **Multi-Agent Orchestration + Prompt Caching** | Build Scout Agent (job discovery), Match Agent (resume scoring), and wire them into Hunter's LangGraph as sub-graph nodes. Implement prompt caching to eliminate redundant token burns on stable system prompts. |
| **Week 6** | MCP Advanced Tools | Browser automation, Notion integration, file system management. |
| **Week 7** | Apply & Outreach Automation | Cover letter drafting, application submission, recruiter networking. |
| **Week 8** | Fully Autonomous Mode | Hunter runs overnight job hunts, ranks & applies without any manual input. |

---

<div align="center">

**Built with 🤍 and a dream of never manually applying to jobs again.**

*"Good evening, sir. Shall I begin the hunt?"* — Hunter 🏹

</div>
