/* skill2web adapter: anthropic-chat
   Wraps Anthropic Messages API (https://api.anthropic.com/v1/messages).
   Requires the user to opt-in to dangerous-direct-browser-access.

   Required globals (provided by skeleton runtime):
     state.settings.{llmKey, llmBaseUrl, llmModel}
     LLM_TIMEOUT_MS
     ERROR_UX
*/
async function callLLM(messages, opts) {
  const s = state.settings;
  const url = (s.llmBaseUrl || "https://api.anthropic.com/v1") + "/messages";
  // Split system / user-assistant turns for Anthropic shape.
  const sysParts = messages.filter(m => m.role === "system").map(m => m.content);
  const turns    = messages.filter(m => m.role !== "system").map(m => ({
    role: m.role === "assistant" ? "assistant" : "user",
    content: m.content,
  }));
  const body = {
    model: s.llmModel,
    max_tokens: 4096,
    messages: turns,
    temperature: (opts && opts.temperature != null) ? opts.temperature : 0.4,
  };
  if (sysParts.length) body.system = sysParts.join("\n\n");
  // Anthropic JSON mode: rely on prompt; no native response_format.
  // (opts.json_mode === "response-format" is silently ignored — see ERROR_UX.json_parse fallback.)

  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), LLM_TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "x-api-key":          s.llmKey,
        "anthropic-version":  "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
        "Content-Type":       "application/json",
      },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!resp.ok) {
      const t = await resp.text();
      const msg = (resp.status >= 400 && resp.status < 500) ? ERROR_UX.llm_4xx : ERROR_UX.llm_5xx;
      throw new Error(`LLM ${resp.status}: ${msg} | ${t.slice(0, 200)}`);
    }
    const j = await resp.json();
    // Anthropic response: { content: [ { type: "text", text: "..." }, ... ] }
    return (j.content || []).filter(c => c.type === "text").map(c => c.text).join("");
  } catch (e) {
    if (e.name === "AbortError") throw new Error(ERROR_UX.llm_timeout);
    throw e;
  } finally { clearTimeout(tid); }
}
