/* skill2web adapter: openai-images-compat
   Wraps OpenAI / 兼容 endpoint /v1/images/generations 与 /v1/images/edits.
   Composer inlines this verbatim into the output HTML's <script>.

   Required globals (provided by skeleton runtime):
     state.settings.{imageKey, imageBaseUrl, imageModel, imageEndpointMode}
     IMAGE_TIMEOUT_MS
     ERROR_UX
*/
async function callImageAPI(prompt, size, defaultEndpointMode) {
  const s = state.settings;
  const mode = s.imageEndpointMode || defaultEndpointMode || "generations";
  if (mode === "generations") return callImageGenerations(prompt, size);
  return callImageEdits(prompt, size);
}

async function callImageGenerations(prompt, size) {
  const s = state.settings;
  const url = s.imageBaseUrl + "/images/generations";
  const body = { model: s.imageModel, prompt, n: 1, size, response_format: "b64_json" };
  return await imageFetch(url, body, true);
}

async function callImageEdits(prompt, size) {
  const s = state.settings;
  const url = s.imageBaseUrl + "/images/edits";
  const [w, h] = size.split("x").map(n => parseInt(n, 10));
  const blank = await makeBlankPng(w, h);
  const fd = new FormData();
  fd.append("model", s.imageModel);
  fd.append("prompt", prompt);
  fd.append("size", size);
  fd.append("n", "1");
  fd.append("image", blank, "blank.png");
  return await imageFetch(url, fd, false);
}

async function imageFetch(url, body, isJson) {
  const s = state.settings;
  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), IMAGE_TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: isJson
        ? { "Authorization": "Bearer " + s.imageKey, "Content-Type": "application/json" }
        : { "Authorization": "Bearer " + s.imageKey },
      body: isJson ? JSON.stringify(body) : body,
      signal: ctrl.signal,
    });
    if (!resp.ok) {
      const t = await resp.text();
      const msg = (resp.status >= 400 && resp.status < 500) ? ERROR_UX.image_4xx : ERROR_UX.image_5xx;
      throw new Error(`image ${resp.status}: ${msg} | ${t.slice(0, 200)}`);
    }
    const j = await resp.json();
    const item = j.data?.[0];
    if (!item) throw new Error("响应缺 data[0]");
    if (item.b64_json) return item.b64_json;
    if (item.url) {
      const ir = await fetch(item.url); const blob = await ir.blob();
      return await blobToBase64(blob);
    }
    throw new Error("响应缺 b64_json/url");
  } catch (e) {
    if (e.name === "AbortError") throw new Error(ERROR_UX.image_timeout);
    throw e;
  } finally { clearTimeout(tid); }
}

function makeBlankPng(w, h) {
  return new Promise((resolve) => {
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const ctx = c.getContext("2d"); ctx.fillStyle = "#FBFAF5"; ctx.fillRect(0, 0, w, h);
    c.toBlob(b => resolve(b), "image/png");
  });
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => { const s = String(r.result); const i = s.indexOf(","); resolve(i >= 0 ? s.slice(i + 1) : s); };
    r.onerror = reject;
    r.readAsDataURL(blob);
  });
}
