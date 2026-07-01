#!/usr/bin/env python3
import os

def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

plan_md = """app: det-practice-app
platform: web (docker, WSL2, no GPU)
total_sessions: 7

overview: A Dockerized Duolingo English Test (DET) practice web app. Single FastAPI backend (Python) serves both a JSON API under /api and a plain HTML/JS/CSS frontend as static files, so only one container is needed. Eight practice tasks: Read & Select (real/fake word), Read & Complete (fill blanks), Interactive Reading (passage + MCQ), Interactive Listening (script read aloud via browser TTS + MCQ), Write About the Photo (Gemini multimodal scoring), Speaking Practice (record, Groq transcribe, Gemini feedback), Writing Sample (timed essay, Gemini feedback), Speaking Sample (timed recorded response, Groq + Gemini feedback). Tasks 1-4 are graded client-side against an embedded answer key and logged to history via one shared endpoint; tasks 5-8 are graded server-side by calling Gemini (text+image) and Groq (speech-to-text) free-tier cloud APIs, and every AI-scored task returns a 10-160 DET-style score_estimate plus exactly 3 tips. History and a simple per-task stats dashboard are stored in SQLite. Runs via docker compose up --build, binds 0.0.0.0, published on localhost:8000 for the Windows browser under WSL2.

contracts: |
  REST_API (prefix /api, JSON unless noted; all routers registered under this prefix in app/main.py):
    GET  /api/read-select/questions?count=10        -> {"items":[{"id":int,"word":str,"is_real":bool}]}
    GET  /api/read-complete/questions?count=5        -> {"items":[{"id":int,"text_with_blanks":str,"blanks":[str,...]}]}
      text_with_blanks uses the literal marker ___ (3 underscores) once per blank, in order matching blanks.
    GET  /api/interactive-reading/passage            -> {"id":int,"title":str,"text":str,"questions":[{"qid":int,"question":str,"options":[str,str,str,str],"correct_index":int}]}
    GET  /api/interactive-listening/item             -> {"id":int,"script_lines":[{"speaker":str,"text":str}],"questions":[{"qid":int,"question":str,"options":[str,...],"correct_index":int}]}
    GET  /api/history?task_type=&limit=50            -> {"entries":[{"id":int,"task_type":str,"score":float,"detail":object,"created_at":str}]}
    GET  /api/history/stats                          -> {"stats":[{"task_type":str,"count":int,"avg_score":float}]}
    POST /api/history/log   body {"task_type":str,"score":float,"detail":object} -> {"id":int,"created_at":str}
      task_type values used by tasks 1-4: read_select, read_complete, interactive_reading, interactive_listening
      score for tasks 1-4 is client-computed percentage 0-100; detail is free-form e.g. {"total":int,"correct":int}
    GET  /api/write-photo/prompt                     -> {"id":int,"image_url":str,"instruction":str}
    POST /api/write-photo/submit   body {"prompt_id":int,"image_url":str,"description":str} -> AIScoreResult
    GET  /api/speaking-practice/prompt               -> {"id":int,"prompt_text":str}
    POST /api/speaking-practice/submit  multipart/form-data fields: audio=<file blob>, prompt_id=<int> -> AIScoreResult (transcript present)
    GET  /api/writing-sample/prompt                  -> {"id":int,"prompt_text":str,"time_limit_seconds":int}
    POST /api/writing-sample/submit  body {"prompt_id":int,"essay":str} -> AIScoreResult
    GET  /api/speaking-sample/prompt                 -> {"id":int,"prompt_text":str,"time_limit_seconds":int}
    POST /api/speaking-sample/submit  multipart/form-data fields: audio=<file blob>, prompt_id=<int> -> AIScoreResult (transcript present)
    AIScoreResult = {"score_estimate":int (10-160 DET scale),"tips":[str,str,str],"transcript":str or null}
      routers for write-photo/speaking-practice/writing-sample/speaking-sample call database.save_attempt(task_type,
      score_estimate/160*100, detail) directly in-process after scoring (no HTTP hop to /api/history/log); detail =
      the full AIScoreResult dict plus "prompt_id". task_type values: write_photo, speaking_practice, writing_sample, speaking_sample.

  PYTHON_MODULE_INTERFACES (authored in session 1; imported by name in later sessions, do not redefine):
    app/config.py: exposes GEMINI_API_KEY:str, GROQ_API_KEY:str, DB_PATH:str (default "/app/storage/det_practice.db",
      overridable via env var DB_PATH), HOST:str (default "0.0.0.0"), PORT:int (default 8000). Loads .env via python-dotenv.
    app/database.py: init_db() -> None (creates table attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT,
      score REAL, detail_json TEXT, created_at TEXT) at DB_PATH, creating parent dir if missing);
      save_attempt(task_type: str, score: float, detail: dict) -> dict {"id":int,"created_at":str};
      get_history(task_type: str = None, limit: int = 50) -> list[dict] (id, task_type, score, detail as parsed dict,
      created_at, newest first); get_stats() -> list[dict] {"task_type":str,"count":int,"avg_score":float}.
      created_at is generated and returned as datetime.now(timezone.utc).isoformat().
    app/gemini_client.py: score_with_gemini(instruction: str, content_text: str, image_bytes: bytes = None,
      image_mime_type: str = None) -> dict {"score_estimate":int,"tips":[str,str,str]}. Literal call shape:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        parts = [content_text] if image_bytes is None else [content_text, types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type)]
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=parts,
            config=types.GenerateContentConfig(system_instruction=instruction, response_mime_type="application/json"),
        )
        result = json.loads(response.text)
      The instruction/system_instruction must direct the model to return ONLY a JSON object with exactly the keys
      score_estimate (int 10-160, DET overall-score style) and tips (array of exactly 3 short actionable strings).
      Hazard: on any exception or JSON parse failure, return this fixed fallback dict instead of raising, so routers
      never 500 on an AI hiccup:
        {"score_estimate": 80, "tips": ["We could not generate detailed feedback this time, please try again.",
        "Aim for clear structure and relevant vocabulary.", "Practice at a natural, steady pace."]}
    app/groq_client.py: transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str. Literal call shape:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes), model="whisper-large-v3-turbo", response_format="json", language="en",
        )
        return transcription.text
      Hazard: on any exception, return "" instead of raising; the calling router must treat "" as "no speech detected"
      and still call gemini_client with a note that no transcript was available, never crash.
      Hazard: Groq audio uploads are capped at 25MB; recorder.js should not allow recordings beyond a few minutes.
    app/question_bank.py: loads app/data/questions.json once at import time; exposes
      get_read_select_batch(count:int=10)->list[dict]{id,word,is_real}
      get_read_complete_batch(count:int=5)->list[dict]{id,text_with_blanks,blanks}
      get_reading_passage()->dict{id,title,text,questions} (same fields as GET /api/interactive-reading/passage)
      get_listening_item()->dict{id,script_lines,questions} (same fields as GET /api/interactive-listening/item)
      get_photo_prompt()->dict{id,image_url,instruction} (image_url values are stable picsum.photos URLs baked into
        questions.json, e.g. "https://picsum.photos/id/1015/800/600"; no image API key needed)
      get_speaking_practice_prompts()->list[dict]{id,prompt_text}
      get_writing_sample_prompts()->list[dict]{id,prompt_text}
      get_speaking_sample_prompts()->list[dict]{id,prompt_text}
      Any function serving one of several items picks pseudo-randomly via random.choice per call.
    Request/response bodies: implement inline per-router Pydantic models or plain dict returns, exact shapes are
      pinned in REST_API above; no shared schemas module is needed since FastAPI accepts dicts via Body() and
      returns dicts directly (auto-serialized to JSON).

  FRONTEND_JS_INTERFACES (authored across sessions 4-6; every task file must follow this exact registry pattern):
    window.DETApi (static/js/api.js) = {
      get(path) -> Promise<object>,               fetch("/api"+path).then(r=>r.json())
      postJson(path, body) -> Promise<object>,     JSON POST, base "/api"
      postForm(path, formData) -> Promise<object>, multipart POST (FormData), base "/api"
    }
    window.DETRecorder (static/js/recorder.js) = { start() -> Promise<void>, stop() -> Promise<Blob> }
      Uses navigator.mediaDevices.getUserMedia({audio:true}) + MediaRecorder. getUserMedia works over plain http
      because the app is accessed via http://localhost, which browsers treat as a secure-context exception, no
      HTTPS or cert needed for WSL2 localhost access. Blob mimeType is whatever MediaRecorder reports (typically
      audio/webm); stop() resolves with that Blob so callers can pick the filename extension from blob.type.
    window.DETTts (static/js/tts.js) = { speak(text, opts) -> Promise<void>, speakLines(lines, opts) -> Promise<void> }
      lines: [{speaker,text}]. Wraps window.speechSynthesis; speakLines speaks each line's text in order, awaiting
      each utterance's 'end' event before starting the next.
    window.DET_TASKS (populated by each static/js/task_<key>.js file; app.js only reads this registry, never file names)
      window.DET_TASKS["<key>"] = { title: str, init: function(containerEl) {} }
      Exact keys (must match filenames task_<key>.js and the history task_type values used above where applicable):
        read_select, read_complete, interactive_reading, interactive_listening,
        write_photo, speaking_practice, writing_sample, speaking_sample
    TASK_MANIFEST (hardcoded in static/js/app.js, the single place the 8 task filenames are listed):
      [{key:"read_select", file:"task_read_select.js", title:"Read and Select"},
       {key:"read_complete", file:"task_read_complete.js", title:"Read and Complete"},
       {key:"interactive_reading", file:"task_interactive_reading.js", title:"Interactive Reading"},
       {key:"interactive_listening", file:"task_interactive_listening.js", title:"Interactive Listening"},
       {key:"write_photo", file:"task_write_photo.js", title:"Write About the Photo"},
       {key:"speaking_practice", file:"task_speaking_practice.js", title:"Speaking Practice"},
       {key:"writing_sample", file:"task_writing_sample.js", title:"Writing Sample"},
       {key:"speaking_sample", file:"task_speaking_sample.js", title:"Speaking Sample"}]
      app.js injects one <script src="js/"+file> per manifest entry at startup (before rendering nav), then waits
      for all to load (script.onload) before enabling navigation, so window.DET_TASKS is fully populated before the
      user can click a task. index.html itself only has <script> tags for api.js, recorder.js, tts.js, app.js (in
      that order); app.js does the rest, so index.html never needs to know sessions 5-6 filenames directly.

  DESIGN: light, calm, education-app aesthetic, soft blue/green accent palette, generous whitespace, card-based task
    dashboard, one task rendered at a time inside a single #task-container element that init() swaps content into.

  ENV_VARS (.env, read by app/config.py): GEMINI_API_KEY, GROQ_API_KEY. Optional: DB_PATH, PORT.

  DOCKER: single service, image built from repo root Dockerfile (python:3.12-slim base), WORKDIR /app, copies
    requirements.txt + app/ + static/, pip install --no-cache-dir -r requirements.txt, creates /app/storage,
    EXPOSE 8000, CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]. docker-compose.yml: one service,
    build context ".", ports "8000:8000", env_file ".env", volumes named "det_storage:/app/storage" for SQLite
    persistence across restarts, restart: unless-stopped.
    Hazard: in app/main.py, register all /api routers via include_router BEFORE mounting StaticFiles at "/", and
    mount StaticFiles last with html=True, otherwise the static catch-all can shadow API routes.

stack: |
  python@3.12
  fastapi==0.136.1
  uvicorn==0.49.0
  pydantic==2.10.4
  python-multipart==0.0.30
  python-dotenv==1.0.1
  google-genai==2.8.0
  groq==1.5.0
  requests==2.32.3

sessions:
  1: [app/config.py, app/database.py, app/gemini_client.py, app/groq_client.py, app/question_bank.py, app/data/questions.json, requirements.txt]
  2: [app/routers/read_select.py, app/routers/read_complete.py, app/routers/interactive_reading.py, app/routers/interactive_listening.py, app/routers/history.py]
  3: [app/routers/write_photo.py, app/routers/speaking_practice.py, app/routers/writing_sample.py, app/routers/speaking_sample.py]
  4: [static/index.html, static/css/style.css, static/js/api.js, static/js/recorder.js, static/js/tts.js, static/js/app.js]
  5: [static/js/task_read_select.js, static/js/task_read_complete.js, static/js/task_interactive_reading.js, static/js/task_interactive_listening.js]
  6: [static/js/task_write_photo.js, static/js/task_speaking_practice.js, static/js/task_writing_sample.js, static/js/task_speaking_sample.js]
  7: [app/main.py, Dockerfile, docker-compose.yml, .env.example]

next_schema:
  session: [N]
  files: [file list from sessions[N]]
  handoff_out: artifacts/handoff_[N].md
  is_last: [true|false]
  read_handoffs: [comma-separated prior concise handoff paths; empty for session 1]

build_protocol steps:
  1  read next.md -> {session=N, files, handoff_out, is_last, read_handoffs}
  2  read plan.md -> {stack, contracts, total_sessions}
  3  read each path in read_handoffs in order (skip if empty)
  4  emit open(path,"w").write(...) calls for every file in files, full content, no stubs; never output file contents as raw text or with separator comments
  5  write concise handoff_out (flat key:value):
       part1: new contracts not in plan.md contracts, omit section entirely if none
       part2: file paths produced this session
  6  if is_last=false -> overwrite artifacts/next.md:
       session: N+1
       files: sessions[N+1] from plan.md
       handoff_out: artifacts/handoff_[N+1].md
       is_last: (N+1 == total_sessions)
       read_handoffs: handoff_1.md, ..., handoff_N.md (all produced so far)
  7  if is_last=true -> write README.md, .gitignore, platform build-ignore file(s); leave next.md unchanged
  delivery: single fenced python code block in the chat reply only, never written to disk, executed, installed, or attached as a file; paths relative to cwd exactly as listed, no wrapper folder; binary assets noted in README, not written; the user runs the script locally
  script_rule: in Markdown file content strings use ~~~ as fence delimiters, not triple backticks, triple backticks inside a Python triple-quoted string break the outer fenced code block display
  on_contradiction: smallest literal fix -> log in handoff part1 as flagged_correction -> proceed; no redesign
  ownership: write only files in next.md; never re-output prior or future sessions' files
  stack_lock: no dependency outside plan.md stack
  no_verification: trust plan.md completely, no installs, imports, version checks, server starts, or test runs of any kind; the sandbox's network/runtime doesn't reflect the deploy target
  no_narration: execute steps directly; do not restate next.md/plan.md contents in prose first
  write_means: "write" in every step above means emit a Python open(path,"w").write(...) call, never display file contents as raw text, inline code, or with # === filename === separators
"""

next_md = """session: 1
files: app/config.py, app/database.py, app/gemini_client.py, app/groq_client.py, app/question_bank.py, app/data/questions.json, requirements.txt
handoff_out: artifacts/handoff_1.md
is_last: false
read_handoffs:
"""

write_file("artifacts/plan.md", plan_md)
write_file("artifacts/next.md", next_md)

print("Wrote artifacts/plan.md and artifacts/next.md")