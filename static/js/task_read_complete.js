(function () {
  var TASK_KEY = "read_complete";

  function buildItemEl(item) {
    var wrapper = document.createElement("div");
    wrapper.className = "prompt-panel";
    wrapper.style.marginBottom = "16px";

    var segments = item.text_with_blanks.split("___");
    var inputs = [];

    segments.forEach(function (segment, i) {
      wrapper.appendChild(document.createTextNode(segment));
      if (i < segments.length - 1) {
        var input = document.createElement("input");
        input.type = "text";
        input.className = "field";
        input.style.width = "120px";
        input.style.display = "inline-block";
        input.style.margin = "0 4px";
        inputs.push(input);
        wrapper.appendChild(input);
      }
    });

    return { wrapper: wrapper, inputs: inputs };
  }

  function loadTask(containerEl) {
    containerEl.innerHTML = "<p>Loading...</p>";
    window.DETApi
      .get("/read-complete/questions?count=5")
      .then(function (data) {
        render(containerEl, data.items || []);
      })
      .catch(function () {
        containerEl.innerHTML = "<p>Failed to load questions. Please try again.</p>";
      });
  }

  function render(containerEl, items) {
    containerEl.innerHTML = "";

    var header = document.createElement("div");
    header.className = "task-header";
    header.innerHTML =
      "<h2>Read and Complete</h2><p>Fill in each blank with the word that best completes the text, then submit.</p>";
    containerEl.appendChild(header);

    var builtItems = items.map(function (item) {
      var built = buildItemEl(item);
      containerEl.appendChild(built.wrapper);
      return { item: item, inputs: built.inputs };
    });

    var submitBtn = document.createElement("button");
    submitBtn.type = "button";
    submitBtn.className = "btn btn-primary";
    submitBtn.textContent = "Submit";

    var retryBtn = document.createElement("button");
    retryBtn.type = "button";
    retryBtn.className = "btn btn-secondary";
    retryBtn.textContent = "New Set";
    retryBtn.style.marginLeft = "8px";

    var resultEl = document.createElement("p");
    resultEl.style.marginTop = "12px";

    submitBtn.addEventListener("click", function () {
      var correct = 0;
      var total = 0;

      builtItems.forEach(function (entry) {
        entry.item.blanks.forEach(function (answer, i) {
          total += 1;
          var input = entry.inputs[i];
          if (!input) return;
          input.disabled = true;

          var isRight =
            input.value.trim().toLowerCase() === String(answer).trim().toLowerCase();
          input.classList.toggle("is-correct", isRight);
          input.classList.toggle("is-incorrect", !isRight);

          if (isRight) {
            correct += 1;
          } else {
            var hint = document.createElement("span");
            hint.style.marginLeft = "6px";
            hint.style.fontStyle = "italic";
            hint.textContent = "(" + answer + ")";
            input.insertAdjacentElement("afterend", hint);
          }
        });
      });

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

    var actions = document.createElement("div");
    actions.style.marginTop = "16px";
    actions.appendChild(submitBtn);
    actions.appendChild(retryBtn);
    containerEl.appendChild(actions);
    containerEl.appendChild(resultEl);
  }

  window.DET_TASKS = window.DET_TASKS || {};
  window.DET_TASKS["read_complete"] = {
    title: "Read and Complete",
    init: function (containerEl) {
      loadTask(containerEl);
    },
  };
})();
