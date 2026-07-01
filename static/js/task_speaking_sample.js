window.DET_TASKS = window.DET_TASKS || {};

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
