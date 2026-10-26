const $ = (selector) => document.querySelector(selector);
const api = async (path, options = {}) => {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
};
const escapeHtml = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));
const fmtDate = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? escapeHtml(value) : date.toLocaleString();
};
const shortId = (value) => value ? value.slice(0, 8).toUpperCase() : "—";
function setHealth(ok, label) {
  $("#health-label").textContent = label;
  $("#sidebar-status").textContent = ok ? "OPERATIONAL" : "UNAVAILABLE";
  $(".status-chip i").style.background = ok ? "var(--cyan)" : "var(--red)";
  $(".pulse").style.background = ok ? "var(--cyan)" : "var(--red)";
}
async function loadHealth() {
  try { await api("/health"); setHealth(true, "Service operational"); }
  catch { setHealth(false, "API unavailable"); }
}
async function loadAgents() {
  const result = await api("/agents");
  const agents = result.agents || [];
  $("#agent-count").textContent = String(agents.length).padStart(2, "0");
  $("#agent-list").innerHTML = agents.map((agent, index) => `
    <article class="agent-card"><span class="agent-number">AGENT / 0${index + 1}</span>
    <h4>${escapeHtml(agent.name)}</h4><p>${escapeHtml(agent.role)}</p>
    <div class="agent-id">${escapeHtml(agent.id)}</div></article>`).join("");
}
async function loadMissions() {
  const missions = await api("/missions?limit=50");
  $("#mission-count").textContent = String(missions.length).padStart(2, "0");
  if (!missions.length) {
    $("#missions-list").innerHTML = '<div class="empty">No missions yet. Create a draft to begin.</div>';
    return;
  }
  $("#missions-list").innerHTML = missions.map((mission) => `
    <article class="mission-card">
      <div class="mission-card-top"><div><div class="mission-title">${escapeHtml(mission.name)}</div>
      <div class="mission-id">ID · ${escapeHtml(shortId(mission.id))} · ${escapeHtml(mission.environment)}</div></div>
      <span class="status ${escapeHtml(mission.status)}">${escapeHtml(mission.status)}</span></div>
      <p class="mission-objective">${escapeHtml(mission.objective)}</p>
      <div class="mission-actions"><button class="mini-button" data-action="plan" data-id="${escapeHtml(mission.id)}">${mission.status === "planned" || mission.status === "blocked" ? "Re-plan" : "Run planning agents"} →</button>
      <button class="mini-button" data-action="inspect" data-id="${escapeHtml(mission.id)}">Inspect report</button></div>
    </article>`).join("");
}
async function loadEvents() {
  const result = await api("/events?limit=20");
  const events = result.events || [];
  $("#event-count").textContent = String(events.length).padStart(2, "0");
  $("#event-rows").innerHTML = events.length ? events.map((event) => `
    <tr><td>${escapeHtml(event.event_type)}</td><td>${escapeHtml(event.actor)}</td>
    <td>${escapeHtml(shortId(event.mission_id))}</td><td>${escapeHtml(fmtDate(event.created_at))}</td></tr>`).join("") :
    '<tr><td colspan="4" class="empty">No events recorded yet.</td></tr>';
}
async function refreshAll() {
  await loadHealth();
  try { await Promise.all([loadAgents(), loadMissions(), loadEvents()]); }
  catch (error) { setHealth(false, "API error"); console.error(error); }
}
$("#mission-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = $("#form-message");
  const form = new FormData(event.currentTarget);
  const splitList = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
  const payload = {
    name: form.get("name").trim(),
    objective: form.get("objective").trim(),
    environment: form.get("environment"),
    waypoints: splitList(form.get("waypoints") || ""),
    constraints: splitList(form.get("constraints") || ""),
  };
  message.className = "message";
  message.textContent = "Creating mission draft…";
  try {
    const mission = await api("/missions", { method: "POST", body: JSON.stringify(payload) });
    message.className = "message success";
    message.textContent = `Draft created (${shortId(mission.id)}). Run the planning agents from the mission register when ready.`;
    event.currentTarget.reset();
    await Promise.all([loadMissions(), loadEvents()]);
  } catch (error) {
    message.className = "message error";
    message.textContent = error.message;
  }
});
$("#missions-list").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = button.dataset.id;
  try {
    if (button.dataset.action === "plan") {
      button.disabled = true;
      button.textContent = "Planning…";
      const mission = await api(`/missions/${encodeURIComponent(id)}/plan`, { method: "POST" });
      const decision = mission.plan?.decision || "unknown";
      const report = mission.reports.map((item) => `• ${item.agent_name} — ${item.status}: ${item.summary}`).join("\n");
      window.alert(`Mission assessment: ${decision.toUpperCase()}\n\n${report}\n\nNote: Planning only. Human review required; no commands were executed.`);
    } else {
      const mission = await api(`/missions/${encodeURIComponent(id)}`);
      const report = (mission.reports || []).map((item) => `• ${item.agent_name} — ${item.status}: ${item.summary}\n  ${(item.findings || []).join("; ")}`).join("\n\n");
      window.alert(`MISSION: ${mission.name}\nSTATUS: ${mission.status}\n\nOBJECTIVE\n${mission.objective}\n\nPLAN\n${JSON.stringify(mission.plan, null, 2)}\n\nAGENT REPORTS\n${report || "No reports yet. Run planning agents first."}`);
    }
  } catch (error) { window.alert(error.message); }
  finally { await Promise.all([loadMissions(), loadEvents()]); }
});
$("#refresh").addEventListener("click", refreshAll);
$("#missions-refresh").addEventListener("click", loadMissions);
$("#events-refresh").addEventListener("click", loadEvents);
refreshAll();
