(function () {
  const BASE = "/api";

  async function get(path) {
    const res = await fetch(BASE + path);
    if (!res.ok) {
      throw new Error("GET " + path + " failed with status " + res.status);
    }
    return res.json();
  }

  async function postJson(path, body) {
    const res = await fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error("POST " + path + " failed with status " + res.status);
    }
    return res.json();
  }

  async function postForm(path, formData) {
    const res = await fetch(BASE + path, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error("POST " + path + " failed with status " + res.status);
    }
    return res.json();
  }

  window.DETApi = { get: get, postJson: postJson, postForm: postForm };
})();
