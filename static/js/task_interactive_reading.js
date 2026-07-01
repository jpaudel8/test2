(function () {
  var TASK_KEY = "interactive_reading";

  function loadTask(containerEl) {
    containerEl.innerHTML = "<p>Loading...</p>";
    window.DETApi
      .get("/interactive-reading/passage")
      .then(function (data) {
        render(containerEl, data);
      })
      .catch(function () {
        containerEl.innerHTML = "<p>Failed to load passage. Please try again.</p>";
      });
  }

  function render(containerEl, passage) {
    containerEl.innerHTML = "";

    var header = document.createElement("div");
    header.className = "task-header";
    header.innerHTML =
      "<h2>Interactive Reading</h2><p>Read the passage, then answer the questions below.</p>";
    containerEl.appendChild(header);

    var panel = document.createElement("div");
    panel.className = "prompt-panel";

    var titleEl = document.createElement("h3");
    titleEl.textContent = passage.title;

    var textEl = document.createElement("p");
    textEl.style.whiteSpace = "pre-wrap";
    textEl.textContent = passage.text;

    panel.appendChild(titleEl);
    panel.appendChild(textEl);
    containerEl.appendChild(panel);

    var answers = {};
    var questionEls = [];

    passage.questions.forEach(function (q) {
      var qWrapper = document.createElement("div");
      qWrapper.style.marginTop = "16px";

      var qTitle = document.createElement("p");
      qTitle.textContent = q.question;
      qWrapper.appendChild(qTitle);

      var list = document.createElement("div");
      list.className = "option-list";

      q.options.forEach(function (opt, idx) {
        var card = document.createElement("label");
        card.className = "option-card";

        var input = document.createElement("input");
        input.type = "radio";
        input.name = "q_" + q.qid;
        input.value = String(idx);
        input.addEventListener("change", function () {
          answers[q.qid] = idx;
          list.querySelectorAll(".option-card").forEach(function (c) {
            c.classList.remove("is-selected");
          });
          card.classList.add("is-selected");
        });

        var span = document.createElement("span");
        span.textContent = opt;

        card.appendChild(input);
        card.appendChild(span);
        list.appendChild(card);
      });

      qWrapper.appendChild(list);
      containerEl.appendChild(qWrapper);
      questionEls.push({ q: q, list: list });
    });

    var submitBtn = document.createElement("button");
    submitBtn.type = "button";
    submitBtn.className = "btn btn-primary";
    submitBtn.textContent = "Submit";
    submitBtn.style.marginTop = "16px";

    var retryBtn = document.createElement("button");
    retryBtn.type = "button";
    retryBtn.className = "btn btn-secondary";
    retryBtn.textContent = "New Passage";
    retryBtn.style.marginLeft = "8px";

    var resultEl = document.createElement("p");
    resultEl.style.marginTop = "12px";

    submitBtn.addEventListener("click", function () {
      var correct = 0;

      questionEls.forEach(function (entry) {
        var q = entry.q;
        var list = entry.list;
        var selected = answers[q.qid];
        var cards = list.querySelectorAll(".option-card");

        cards.forEach(function (c) {
          c.querySelector("input").disabled = true;
        });

        var isRight = selected === q.correct_index;
        if (isRight) correct += 1;

        cards.forEach(function (c, idx) {
          if (idx === q.correct_index) {
            c.classList.add("is-correct");
          } else if (idx === selected) {
            c.classList.add("is-incorrect");
          }
        });
      });

      var total = passage.questions.length;
      var score = total > 0 ? Math.round((correct / total) * 100) : 0;
      resultEl.textContent = "Score: " + correct + " / " + total + " (" + score + "%)";
      submitBtn.disabled = true;

      window.DETApi
        .postJson("/history/log", {
          task_type: TASK_KEY,
          score: score,
          detail: { total: total, correct: correct },
        })
        .catch(function () {});
    });

    retryBtn.addEventListener("click", function () {
      loadTask(containerEl);
    });

    containerEl.appendChild(submitBtn);
    containerEl.appendChild(retryBtn);
    containerEl.appendChild(resultEl);
  }

  window.DET_TASKS = window.DET_TASKS || {};
  window.DET_TASKS["interactive_reading"] = {
    title: "Interactive Reading",
    init: function (containerEl) {
      loadTask(containerEl);
    },
  };
})();
