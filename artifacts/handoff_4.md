session: 4
new_contracts: |
  CSS_COMPONENT_CLASSES (static/css/style.css, available globally for task_<key>.js modules built in sessions 5-6):
    .task-header, .task-header h2, .task-header p -> task title/instructions block
    .btn, .btn-primary, .btn-secondary, .btn-danger -> action buttons (secondary for neutral actions, danger for
      destructive/reset actions)
    .field (apply to input.field or textarea.field) -> standard text input/textarea styling
    .option-list > .option-card (label wrapping input[type=radio|checkbox] plus text) -> MCQ/answer choice rows;
      toggle class is-selected while chosen, is-correct/is-incorrect after grading to color the row
    .prompt-panel -> boxed prompt/passage/photo display area; prompt-panel img for photo prompts
    .timer-display (add is-low class when time is running out) -> countdown display for timed tasks
    .feedback-banner containing .score-badge (with nested .score-scale span, e.g. for "/160") and a ul list ->
      AI feedback / tips display after an AIScoreResult submission
    .transcript-box -> italic boxed area for displaying a returned transcript string
    .spinner -> small inline loading spinner span
    .record-indicator containing a .dot span -> pulsing "recording" state label for speaking tasks
  DASHBOARD_BEHAVIOR (static/js/app.js; task modules never need to touch this themselves):
    task_<key>.js files only need to set window.DET_TASKS["<key>"] = {title, init(containerEl)}; app.js clears and
      shows #task-container automatically before calling init(), and the always-visible "Back to dashboard" button
      re-renders the dashboard, including a refreshed GET /api/history/stats fetch, with no action required from
      task code.
    init(containerEl) receives an already-emptied container inside #task-view; task modules should render entirely
      within it and are free to use the CSS_COMPONENT_CLASSES above for visual consistency with the rest of the app.
    The dashboard stats strip renders one .stat-card per task_type returned by GET /api/history/stats, showing
      avg_score rounded to a whole-number percent; new task_type values from sessions 5-6 appear automatically, no
      dashboard change is needed when those sessions add task modules.
files_produced: static/index.html, static/css/style.css, static/js/api.js, static/js/recorder.js, static/js/tts.js, static/js/app.js
