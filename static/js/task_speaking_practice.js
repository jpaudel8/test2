window.DET_TASKS = window.DET_TASKS || {};

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
