(function () {
  const TASK_MANIFEST = [
    { key: "read_select", file: "task_read_select.js", title: "Read and Select", blurb: "Spot real English words among decoys." },
    { key: "read_complete", file: "task_read_complete.js", title: "Read and Complete", blurb: "Fill the blanks in a short passage." },
    { key: "interactive_reading", file: "task_interactive_reading.js", title: "Interactive Reading", blurb: "Read a passage, then answer questions." },
    { key: "interactive_listening", file: "task_interactive_listening.js", title: "Interactive Listening", blurb: "Listen to a short exchange, then answer." },
    { key: "write_photo", file: "task_write_photo.js", title: "Write About the Photo", blurb: "Describe an image and get AI feedback." },
    { key: "speaking_practice", file: "task_speaking_practice.js", title: "Speaking Practice", blurb: "Record a short answer and get AI feedback." },
    { key: "writing_sample", file: "task_writing_sample.js", title: "Writing Sample", blurb: "Write a timed essay and get AI feedback." },
    { key: "speaking_sample", file: "task_speaking_sample.js", title: "Speaking Sample", blurb: "Record a timed response and get AI feedback." },
  ];

  window.DET_TASKS = window.DET_TASKS || {};

  document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("back-button").addEventListener("click", showDashboard);
    loadTaskScripts()
      .then(function () {
        renderDashboard();
      })
      .catch(function (err) {
        renderLoadError(err);
      });
  });

  function loadTaskScripts() {
    const loads = TASK_MANIFEST.map(function (task) {
      return new Promise(function (resolve, reject) {
        const script = document.createElement("script");
        script.src = "js/" + task.file;
        script.addEventListener("load", function () { resolve(task.key); });
        script.addEventListener("error", function () {
          reject(new Error("Failed to load task module: " + task.file));
        });
        document.body.appendChild(script);
      });
    });
    return Promise.all(loads);
  }

  function renderLoadError(err) {
    const grid = document.getElementById("task-grid");
    grid.innerHTML = "";
    const notice = document.createElement("div");
    notice.className = "stats-empty";
    notice.textContent = "Some practice tasks could not be loaded (" + err.message + "). Refresh to try again.";
    grid.appendChild(notice);
    renderStats();
  }

  function renderDashboard() {
    showDashboardView();
    renderStats();
    renderTaskGrid();
  }

  function showDashboardView() {
    document.getElementById("dashboard-view").hidden = false;
    document.getElementById("task-view").hidden = true;
  }

  function showDashboard() {
    document.getElementById("task-container").innerHTML = "";
    showDashboardView();
    renderStats();
  }

  function renderTaskGrid() {
    const grid = document.getElementById("task-grid");
    grid.innerHTML = "";
    TASK_MANIFEST.forEach(function (task, index) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "task-card";
      card.setAttribute("data-task-key", task.key);

      const badge = document.createElement("span");
      badge.className = "task-badge tone-" + (index % 4);
      badge.textContent = initials(task.title);
      badge.setAttribute("aria-hidden", "true");

      const heading = document.createElement("h2");
      heading.textContent = task.title;

      const desc = document.createElement("p");
      desc.textContent = task.blurb;

      card.appendChild(badge);
      card.appendChild(heading);
      card.appendChild(desc);
      card.addEventListener("click", function () { openTask(task.key); });
      grid.appendChild(card);
    });
  }

  function initials(title) {
    return title
      .split(" ")
      .filter(function (word) { return word.length > 0; })
      .slice(0, 2)
      .map(function (word) { return word[0].toUpperCase(); })
      .join("");
  }

  function openTask(key) {
    const taskDef = window.DET_TASKS[key];
    const container = document.getElementById("task-container");
    container.innerHTML = "";
    document.getElementById("dashboard-view").hidden = true;
    document.getElementById("task-view").hidden = false;
    if (!taskDef || typeof taskDef.init !== "function") {
      const notice = document.createElement("p");
      notice.textContent = "This task is not available right now.";
      container.appendChild(notice);
      return;
    }
    taskDef.init(container);
  }

  function renderStats() {
    const strip = document.getElementById("stats-strip");
    strip.innerHTML = '<div class="loading-row"><span class="spinner"></span> Loading your progress...</div>';
    window.DETApi.get("/history/stats")
      .then(function (data) {
        const stats = (data && data.stats) || [];
        strip.innerHTML = "";
        if (stats.length === 0) {
          const empty = document.createElement("div");
          empty.className = "stats-empty";
          empty.textContent = "No attempts yet. Start a task below to see your progress here.";
          strip.appendChild(empty);
          return;
        }
        stats.forEach(function (stat) {
          const card = document.createElement("div");
          card.className = "stat-card";
          const value = document.createElement("span");
          value.className = "stat-value";
          value.textContent = Math.round(stat.avg_score) + "%";
          const label = document.createElement("span");
          label.className = "stat-label";
          label.textContent = formatTaskLabel(stat.task_type) + " \u00b7 " + stat.count + " " + (stat.count === 1 ? "attempt" : "attempts");
          card.appendChild(value);
          card.appendChild(label);
          strip.appendChild(card);
        });
      })
      .catch(function () {
        strip.innerHTML = '<div class="stats-empty">Progress stats are unavailable right now.</div>';
      });
  }

  function formatTaskLabel(taskType) {
    const match = TASK_MANIFEST.find(function (task) { return task.key === taskType; });
    return match ? match.title : taskType;
  }
})();
