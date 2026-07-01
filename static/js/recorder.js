(function () {
  let mediaRecorder = null;
  let activeStream = null;
  let chunks = [];

  function start() {
    chunks = [];
    return navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      activeStream = stream;
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.addEventListener("dataavailable", function (event) {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      });
      return new Promise(function (resolve, reject) {
        mediaRecorder.addEventListener("error", function (event) {
          reject(event.error || new Error("Recording failed to start"));
        });
        mediaRecorder.addEventListener("start", function () {
          resolve();
        });
        mediaRecorder.start();
      });
    });
  }

  function stop() {
    return new Promise(function (resolve, reject) {
      if (!mediaRecorder) {
        reject(new Error("No active recording to stop"));
        return;
      }
      mediaRecorder.addEventListener("stop", function () {
        const mimeType = mediaRecorder.mimeType || "audio/webm";
        const blob = new Blob(chunks, { type: mimeType });
        if (activeStream) {
          activeStream.getTracks().forEach(function (track) { track.stop(); });
        }
        mediaRecorder = null;
        activeStream = null;
        resolve(blob);
      });
      mediaRecorder.stop();
    });
  }

  window.DETRecorder = { start: start, stop: stop };
})();
