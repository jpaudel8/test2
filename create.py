import os

os.makedirs("static/js", exist_ok=True)
os.makedirs("artifacts", exist_ok=True)

open("static/js/task_write_photo.js", "w").write("""window.DET_TASKS = window.DET_TASKS || {};

window.DET_TASKS["write_photo"] = {
  title: "Write About the Photo",
  init: function (containerEl) {
    containerEl.innerHTML = `
      <div class="task-header">
        <h2>Write About the Photo</h2>
        <p>Look at the photo and write one or two sentences describing it.</p>
      </div>
      <div id="wp-body">
        <p>Loading prompt...</p>
      </div>
    `;

    const body = containerEl.querySelector("#wp-body");
    let currentPrompt = null;

    DETApi.get("/write-photo/prompt")
      .then((prompt) => {
        currentPrompt = prompt;
        renderPrompt();
      })
      .catch(() => {
        body.innerHTML = `<p>Could not load a prompt. Please try again later.</p>`;
      });

    function renderPrompt() {
      body.innerHTML = `
        <div class="prompt-panel">
          <img src="${currentPrompt.image_url}" alt="Photo prompt" />
          <p>${currentPrompt.instruction}</p>
        </div>
        <textarea class="field" id="wp-description" rows="5" placeholder="Describe the photo..."></textarea>
        <div>
          <button class="btn btn-primary" id="wp-submit">Submit</button>
          <button class="btn btn-secondary" id="wp-reset">Reset</button>
        </div>
        <div id="wp-feedback"></div>
      `;

      const textarea = body.querySelector("#wp-description");
      const submitBtn = body.querySelector("#wp-submit");
      const resetBtn = body.querySelector("#wp-reset");
      const feedbackEl = body.querySelector("#wp-feedback");

      resetBtn.addEventListener("click", () => {
        textarea.value = "";
        feedbackEl.innerHTML = "";
      });

      submitBtn.addEventListener("click", () => {
        const description = textarea.value.trim();
        if (!description) {
          return;
        }
        submitBtn.disabled = true;
        resetBtn.disabled = true;
        feedbackEl.innerHTML = `<span class="spinner"></span> Scoring your response...`;

        DETApi.postJson("/write-photo/submit", {
          prompt_id: currentPrompt.id,
          image_url: currentPrompt.image_url,
          description: description,
        })
          .then((result) => {
            renderFeedback(feedbackEl, result);
          })
          .catch(() => {
            feedbackEl.innerHTML = `<p>Something went wrong scoring your response. Please try again.</p>`;
          })
          .finally(() => {
            submitBtn.disabled = false;
            resetBtn.disabled = false;
          });
      });
    }

    function renderFeedback(el, result) {
      const tipsHtml = result.tips.map((t) => `<li>${t}</li>`).join("");
      el.innerHTML = `
        <div class="feedback-banner">
          <div class="score-badge">${result.score_estimate}<span class="score-scale">/160</span></div>
          <ul>${tipsHtml}</ul>
        </div>
      `;
    }
  },
};
""")

open("static/js/task_speaking_practice.js", "w").write("""window.DET_TASKS = window.DET_TASKS || {};

window.DET_TASKS["speaking_practice"] = {
  title: "Speaking Practice",
  init: function (containerEl) {
    containerEl.innerHTML = `
      <div class="task-header">
        <h2>Speaking Practice</h2>
        <p>Read the prompt aloud and record your response.</p>
      </div>
      <div id="sp-body">
        <p>Loading prompt...</p>
      </div>
    `;

    const body = containerEl.querySelector("#sp-body");
    let currentPrompt = null;
    let recording = false;

    DETApi.get("/speaking-practice/prompt")
      .then((prompt) => {
        currentPrompt = prompt;
        renderPrompt();
      })
      .catch(() => {
        body.innerHTML = `<p>Could not load a prompt. Please try again later.</p>`;
      });

    function renderPrompt() {
      body.innerHTML = `
        <div class="prompt-panel">
          <p>${currentPrompt.prompt_text}</p>
        </div>
        <div>
          <button class="btn btn-primary" id="sp-record">Start Recording</button>
          <button class="btn btn-danger" id="sp-stop" disabled>Stop Recording</button>
        </div>
        <div id="sp-status"></div>
        <div id="sp-feedback"></div>
      `;

      const recordBtn = body.querySelector("#sp-record");
      const stopBtn = body.querySelector("#sp-stop");
      const statusEl = body.querySelector("#sp-status");
      const feedbackEl = body.querySelector("#sp-feedback");

      recordBtn.addEventListener("click", () => {
        feedbackEl.innerHTML = "";
        DETRecorder.start()
          .then(() => {
            recording = true;
            recordBtn.disabled = true;
            stopBtn.disabled = false;
            statusEl.innerHTML = `<span class="record-indicator"><span class="dot"></span>Recording...</span>`;
          })
          .catch(() => {
            statusEl.innerHTML = `<p>Could not access the microphone. Please check permissions.</p>`;
          });
      });

      stopBtn.addEventListener("click", () => {
        if (!recording) {
          return;
        }
        recording = false;
        stopBtn.disabled = true;
        statusEl.innerHTML = `<span class="spinner"></span> Processing your recording...`;

        DETRecorder.stop().then((blob) => {
          const extension = blob.type.includes("wav") ? "wav" : "webm";
          const formData = new FormData();
          formData.append("audio", blob, "audio." + extension);
          formData.append("prompt_id", currentPrompt.id);

          DETApi.postForm("/speaking-practice/submit", formData)
            .then((result) => {
              statusEl.innerHTML = "";
              recordBtn.disabled = false;
              renderFeedback(feedbackEl, result);
            })
            .catch(() => {
              statusEl.innerHTML = "";
              recordBtn.disabled = false;
              feedbackEl.innerHTML = `<p>Something went wrong scoring your response. Please try again.</p>`;
            });
        });
      });
    }

    function renderFeedback(el, result) {
      const tipsHtml = result.tips.map((t) => `<li>${t}</li>`).join("");
      const transcriptHtml = result.transcript
        ? `<div class="transcript-box">${result.transcript}</div>`
        : `<div class="transcript-box">No speech detected.</div>`;
      el.innerHTML = `
        ${transcriptHtml}
        <div class="feedback-banner">
          <div class="score-badge">${result.score_estimate}<span class="score-scale">/160</span></div>
          <ul>${tipsHtml}</ul>
        </div>
      `;
    }
  },
};
""")

open("static/js/task_writing_sample.js", "w").write("""window.DET_TASKS = window.DET_TASKS || {};

window.DET_TASKS["writing_sample"] = {
  title: "Writing Sample",
  init: function (containerEl) {
    containerEl.innerHTML = `
      <div class="task-header">
        <h2>Writing Sample</h2>
        <p>Write a well-developed response before the timer runs out.</p>
      </div>
      <div id="ws-body">
        <p>Loading prompt...</p>
      </div>
    `;

    const body = containerEl.querySelector("#ws-body");
    let currentPrompt = null;
    let remainingSeconds = 0;
    let timerId = null;
    let submitted = false;

    DETApi.get("/writing-sample/prompt")
      .then((prompt) => {
        currentPrompt = prompt;
        remainingSeconds = prompt.time_limit_seconds;
        renderPrompt();
        startTimer();
      })
      .catch(() => {
        body.innerHTML = `<p>Could not load a prompt. Please try again later.</p>`;
      });

    function renderPrompt() {
      body.innerHTML = `
        <div class="prompt-panel">
          <p>${currentPrompt.prompt_text}</p>
        </div>
        <div class="timer-display" id="ws-timer">${formatTime(remainingSeconds)}</div>
        <textarea class="field" id="ws-essay" rows="10" placeholder="Start writing here..."></textarea>
        <div>
          <button class="btn btn-primary" id="ws-submit">Submit</button>
        </div>
        <div id="ws-feedback"></div>
      `;

      body.querySelector("#ws-submit").addEventListener("click", () => submitEssay(false));
    }

    function formatTime(totalSeconds) {
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return minutes + ":" + String(seconds).padStart(2, "0");
    }

    function startTimer() {
      const timerEl = body.querySelector("#ws-timer");
      timerId = setInterval(() => {
        remainingSeconds -= 1;
        if (remainingSeconds <= 0) {
          remainingSeconds = 0;
          timerEl.textContent = formatTime(0);
          clearInterval(timerId);
          submitEssay(true);
          return;
        }
        timerEl.textContent = formatTime(remainingSeconds);
        if (remainingSeconds <= 30) {
          timerEl.classList.add("is-low");
        }
      }, 1000);
    }

    function submitEssay(auto) {
      if (submitted) {
        return;
      }
      submitted = true;
      if (timerId) {
        clearInterval(timerId);
      }

      const textarea = body.querySelector("#ws-essay");
      const submitBtn = body.querySelector("#ws-submit");
      const feedbackEl = body.querySelector("#ws-feedback");
      const essay = textarea.value.trim();

      submitBtn.disabled = true;
      textarea.disabled = true;
      feedbackEl.innerHTML = `<span class="spinner"></span> Scoring your essay...`;

      DETApi.postJson("/writing-sample/submit", {
        prompt_id: currentPrompt.id,
        essay: essay,
      })
        .then((result) => {
          renderFeedback(feedbackEl, result, auto);
        })
        .catch(() => {
          feedbackEl.innerHTML = `<p>Something went wrong scoring your response. Please try again.</p>`;
        });
    }

    function renderFeedback(el, result, auto) {
      const tipsHtml = result.tips.map((t) => `<li>${t}</li>`).join("");
      const autoNote = auto ? `<p>Time's up! Your essay was submitted automatically.</p>` : "";
      el.innerHTML = `
        ${autoNote}
        <div class="feedback-banner">
          <div class="score-badge">${result.score_estimate}<span class="score-scale">/160</span></div>
          <ul>${tipsHtml}</ul>
        </div>
      `;
    }
  },
};
""")

open("static/js/task_speaking_sample.js", "w").write("""window.DET_TASKS = window.DET_TASKS || {};

window.DET_TASKS["speaking_sample"] = {
  title: "Speaking Sample",
  init: function (containerEl) {
    containerEl.innerHTML = `
      <div class="task-header">
        <h2>Speaking Sample</h2>
        <p>Record a spoken response before the timer runs out.</p>
      </div>
      <div id="ss-body">
        <p>Loading prompt...</p>
      </div>
    `;

    const body = containerEl.querySelector("#ss-body");
    let currentPrompt = null;
    let remainingSeconds = 0;
    let timerId = null;
    let recording = false;
    let finished = false;

    DETApi.get("/speaking-sample/prompt")
      .then((prompt) => {
        currentPrompt = prompt;
        remainingSeconds = prompt.time_limit_seconds;
        renderPrompt();
      })
      .catch(() => {
        body.innerHTML = `<p>Could not load a prompt. Please try again later.</p>`;
      });

    function renderPrompt() {
      body.innerHTML = `
        <div class="prompt-panel">
          <p>${currentPrompt.prompt_text}</p>
        </div>
        <div class="timer-display" id="ss-timer">${formatTime(remainingSeconds)}</div>
        <div>
          <button class="btn btn-primary" id="ss-record">Start Recording</button>
          <button class="btn btn-danger" id="ss-stop" disabled>Stop Recording</button>
        </div>
        <div id="ss-status"></div>
        <div id="ss-feedback"></div>
      `;

      body.querySelector("#ss-record").addEventListener("click", beginRecording);
      body.querySelector("#ss-stop").addEventListener("click", () => finishRecording(false));
    }

    function formatTime(totalSeconds) {
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return minutes + ":" + String(seconds).padStart(2, "0");
    }

    function beginRecording() {
      const recordBtn = body.querySelector("#ss-record");
      const stopBtn = body.querySelector("#ss-stop");
      const statusEl = body.querySelector("#ss-status");

      DETRecorder.start()
        .then(() => {
          recording = true;
          recordBtn.disabled = true;
          stopBtn.disabled = false;
          statusEl.innerHTML = `<span class="record-indicator"><span class="dot"></span>Recording...</span>`;
          startTimer();
        })
        .catch(() => {
          statusEl.innerHTML = `<p>Could not access the microphone. Please check permissions.</p>`;
        });
    }

    function startTimer() {
      const timerEl = body.querySelector("#ss-timer");
      timerId = setInterval(() => {
        remainingSeconds -= 1;
        if (remainingSeconds <= 0) {
          remainingSeconds = 0;
          timerEl.textContent = formatTime(0);
          clearInterval(timerId);
          finishRecording(true);
          return;
        }
        timerEl.textContent = formatTime(remainingSeconds);
        if (remainingSeconds <= 30) {
          timerEl.classList.add("is-low");
        }
      }, 1000);
    }

    function finishRecording(auto) {
      if (finished || !recording) {
        return;
      }
      finished = true;
      recording = false;
      if (timerId) {
        clearInterval(timerId);
      }

      const stopBtn = body.querySelector("#ss-stop");
      const statusEl = body.querySelector("#ss-status");
      const feedbackEl = body.querySelector("#ss-feedback");

      stopBtn.disabled = true;
      statusEl.innerHTML = `<span class="spinner"></span> Processing your recording...`;

      DETRecorder.stop().then((blob) => {
        const extension = blob.type.includes("wav") ? "wav" : "webm";
        const formData = new FormData();
        formData.append("audio", blob, "audio." + extension);
        formData.append("prompt_id", currentPrompt.id);

        DETApi.postForm("/speaking-sample/submit", formData)
          .then((result) => {
            statusEl.innerHTML = auto ? `<p>Time's up! Your response was submitted automatically.</p>` : "";
            renderFeedback(feedbackEl, result);
          })
          .catch(() => {
            statusEl.innerHTML = "";
            feedbackEl.innerHTML = `<p>Something went wrong scoring your response. Please try again.</p>`;
          });
      });
    }

    function renderFeedback(el, result) {
      const tipsHtml = result.tips.map((t) => `<li>${t}</li>`).join("");
      const transcriptHtml = result.transcript
        ? `<div class="transcript-box">${result.transcript}</div>`
        : `<div class="transcript-box">No speech detected.</div>`;
      el.innerHTML = `
        ${transcriptHtml}
        <div class="feedback-banner">
          <div class="score-badge">${result.score_estimate}<span class="score-scale">/160</span></div>
          <ul>${tipsHtml}</ul>
        </div>
      `;
    }
  },
};
""")

open("artifacts/handoff_6.md", "w").write("""session: 6
files_produced: static/js/task_write_photo.js, static/js/task_speaking_practice.js, static/js/task_writing_sample.js, static/js/task_speaking_sample.js
""")

open("artifacts/next.md", "w").write("""session: 7
files: app/main.py, Dockerfile, docker-compose.yml, .env.example
handoff_out: artifacts/handoff_7.md
is_last: true
read_handoffs: artifacts/handoff_1.md, artifacts/handoff_2.md, artifacts/handoff_3.md, artifacts/handoff_4.md, artifacts/handoff_5.md, artifacts/handoff_6.md
""")