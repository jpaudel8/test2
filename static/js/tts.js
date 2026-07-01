(function () {
  function speak(text, opts) {
    opts = opts || {};
    return new Promise(function (resolve, reject) {
      if (!("speechSynthesis" in window)) {
        reject(new Error("Speech synthesis is not supported in this browser"));
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = opts.rate || 1;
      utterance.pitch = opts.pitch || 1;
      if (opts.voice) {
        utterance.voice = opts.voice;
      }
      utterance.addEventListener("end", function () { resolve(); });
      utterance.addEventListener("error", function (event) {
        reject(event.error || new Error("Speech synthesis failed"));
      });
      window.speechSynthesis.speak(utterance);
    });
  }

  async function speakLines(lines, opts) {
    for (const line of lines) {
      await speak(line.text, opts);
    }
  }

  window.DETTts = { speak: speak, speakLines: speakLines };
})();
