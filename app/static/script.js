let chart;

const $ = (id) => document.getElementById(id);
const api = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: {"Content-Type": "application/json"},
    ...options
  });
  if (!response.ok) {
    let detail = "Ошибка запроса";
    try { detail = (await response.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
};

function showMessage(text, error = false) {
  $("message").textContent = text;
  $("message").className = error ? "message error" : "message";
}

function resetForm() {
  $("event-form").reset();
  $("event-id").value = "";
  $("max_attendees").value = 100;
  $("form-title").textContent = "Создать мероприятие";
  $("submit-btn").textContent = "Добавить мероприятие";
  $("cancel-edit").classList.add("hidden");
}

$("cancel-edit").addEventListener("click", resetForm);

$("event-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("event-id").value;
  const payload = {
    title: $("title").value.trim(),
    location: $("location").value.trim(),
    event_date: new Date($("event_date").value).toISOString(),
    max_attendees: Number($("max_attendees").value),
    status: $("status").value,
    description: $("description").value.trim()
  };
  try {
    await api(id ? `/api/events/${id}` : "/api/events", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload)
    });
    showMessage(id ? "Мероприятие обновлено." : "Мероприятие добавлено.");
    resetForm();
    await refresh();
  } catch (err) { showMessage(err.message, true); }
});

function formatDate(value) {
  return new Date(value).toLocaleString("ru-RU", {dateStyle:"medium", timeStyle:"short"});
}
function statusClass(status) {
  if (status === "Завершено") return "done";
  if (status === "Отменено") return "cancel";
  return "";
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

async function loadEvents() {
  const events = await api("/api/events");
  const body = $("events-body");
  if (!events.length) {
    body.innerHTML = '<tr><td colspan="6" class="empty">Пока нет мероприятий. Создайте первое!</td></tr>';
    return;
  }
  body.innerHTML = events.map(ev => `
    <tr>
      <td><strong>${escapeHtml(ev.title)}</strong><span class="subtext">${escapeHtml(ev.description || "")}</span></td>
      <td>${formatDate(ev.event_date)}</td>
      <td>${escapeHtml(ev.location)}</td>
      <td><span class="pill ${statusClass(ev.status)}">${escapeHtml(ev.status)}</span></td>
      <td><div class="attendee"><button onclick="registration(${ev.id},-1)" aria-label="Уменьшить">−</button><b>${ev.registered_count}/${ev.max_attendees}</b><button onclick="registration(${ev.id},1)" aria-label="Увеличить">+</button></div></td>
      <td><div class="row-actions"><button class="action" onclick="editEvent(${ev.id})">Изменить</button><button class="action delete" onclick="deleteEvent(${ev.id})">Удалить</button></div></td>
    </tr>`).join("");
}

async function loadStatistics() {
  const s = await api("/api/statistics");
  ["total","planned","in_progress","participants"].forEach(k => $(k).textContent = s[k]);
  const labels = ["Запланировано","В процессе","Завершено","Отменено"];
  const values = [s.planned,s.in_progress,s.completed,s.cancelled];
  if (chart) chart.destroy();
  chart = new Chart($("status-chart"), {
    type:"doughnut",
    data:{labels,datasets:[{data:values,backgroundColor:["#536dfe","#f2b84b","#159b72","#e46b7a"],borderWidth:0,hoverOffset:5}]},
    options:{maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{usePointStyle:true,boxWidth:7,padding:18,font:{size:11}}}}}
  });
}

async function editEvent(id) {
  try {
    const ev = await api(`/api/events/${id}`);
    $("event-id").value = ev.id;
    $("title").value = ev.title;
    $("location").value = ev.location;
    const d = new Date(ev.event_date);
    $("event_date").value = new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);
    $("max_attendees").value = ev.max_attendees;
    $("status").value = ev.status;
    $("description").value = ev.description || "";
    $("form-title").textContent = "Редактировать мероприятие";
    $("submit-btn").textContent = "Сохранить изменения";
    $("cancel-edit").classList.remove("hidden");
    window.scrollTo({top:0,behavior:"smooth"});
  } catch (err) { showMessage(err.message,true); }
}

async function deleteEvent(id) {
  if (!confirm("Удалить это мероприятие?")) return;
  try { await api(`/api/events/${id}`,{method:"DELETE"}); await refresh(); }
  catch (err) { showMessage(err.message,true); }
}
async function registration(id, delta) {
  try { await api(`/api/events/${id}/registration?delta=${delta}`,{method:"POST"}); await refresh(); }
  catch (err) { showMessage(err.message,true); }
}
async function refresh() {
  try { await Promise.all([loadEvents(),loadStatistics()]); }
  catch (err) { showMessage("Не удалось загрузить данные: "+err.message,true); }
}
refresh();
