/* skill2web adapter: openai-chat-compat
   Wraps OpenAI / DeepSeek / StepFun / 智谱 等 chat completions.
   Composer inlines this verbatim into the output HTML's <script>.

   Required globals (provided by skeleton runtime):
     state.settings.{llmKey, llmBaseUrl, llmModel}
     LLM_TIMEOUT_MS
     ERROR_UX

   Caller passes the step's `temperature` and `json_mode` from llm_pipeline.
*/
async function callLLM(messages, opts) {
  const s = state.settings;
  const url = s.llmBaseUrl + "/chat/completions";
  const body = {
    model: s.llmModel,
    messages,
    temperature: (opts && opts.temperature != null) ? opts.temperature : 0.4,
  };
  if (opts && opts.json_mode === "response-format") {
    body.response_format = { type: "json_object" };
  }
  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), LLM_TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Authorization": "Bearer " + s.llmKey, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!resp.ok) {
      const t = await resp.text();
      const msg = (resp.status >= 400 && resp.status < 500) ? ERROR_UX.llm_4xx : ERROR_UX.llm_5xx;
      throw new Error(`LLM ${resp.status}: ${msg} | ${t.slice(0, 200)}`);
    }
    const j = await resp.json();
    return j.choices?.[0]?.message?.content || "";
  } catch (e) {
    if (e.name === "AbortError") throw new Error(ERROR_UX.llm_timeout);
    throw e;
  } finally { clearTimeout(tid); }
}
