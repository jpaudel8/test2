window.DET_TASKS = window.DET_TASKS || {};

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
