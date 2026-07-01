window.DET_TASKS = window.DET_TASKS || {};

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
