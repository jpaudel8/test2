(function () {
  var TASK_KEY = "read_select";

  function loadTask(containerEl) {
    containerEl.innerHTML = "<p>Loading...</p>";
    window.DETApi
      .get("/read-select/questions?count=10")
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
      "<h2>Read and Select</h2><p>Click each word that is a real English word. Leave fake words unselected, then submit.</p>";
    containerEl.appendChild(header);

    var list = document.createElement("div");
    list.className = "option-list";

    var state = {};

    items.forEach(function (item) {
      state[item.id] = false;

      var card = document.createElement("label");
      card.className = "option-card";
      card.dataset.itemId = String(item.id);

      var input = document.createElement("input");
      input.type = "checkbox";
      input.addEventListener("change", function () {
        state[item.id] = input.checked;
        card.classList.toggle("is-selected", input.checked);
      });

      var span = document.createElement("span");
      span.textContent = item.word;

      card.appendChild(input);
      card.appendChild(span);
      list.appendChild(card);
    });

    containerEl.appendChild(list);

    var actions = document.createElement("div");
    actions.style.marginTop = "16px";

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

      items.forEach(function (item) {
        var card = list.querySelector('[data-item-id="' + item.id + '"]');
        var input = card.querySelector("input");
        input.disabled = true;

        var selected = state[item.id];
        var rightAnswer = selected === item.is_real;
        card.classList.toggle("is-correct", rightAnswer);
        card.classList.toggle("is-incorrect", !rightAnswer);
        if (rightAnswer) correct += 1;
      });

      var total = items.length;
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

    actions.appendChild(submitBtn);
    actions.appendChild(retryBtn);
    containerEl.appendChild(actions);
    containerEl.appendChild(resultEl);
  }

  window.DET_TASKS = window.DET_TASKS || {};
  window.DET_TASKS["read_select"] = {
    title: "Read and Select",
    init: function (containerEl) {
      loadTask(containerEl);
    },
  };
})();
