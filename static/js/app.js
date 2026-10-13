const API_BASE = window.API_BASE_URL !== undefined
  ? window.API_BASE_URL
  : (window.location.port !== "8000" && window.location.protocol.startsWith("http") ? "http://127.0.0.1:8000" : "");

/**
 * OnisAgent Front-end Application
 * Handles chat orchestration, UI tabs, live dashboard updates, and Kev telemetry.
 */

let voice = null;
let savedTokensCount = 0;
let fastPathCount = 0;
let reasoningCount = 0;

document.addEventListener("DOMContentLoaded", () => {
  initVoice();
  initEventListeners();
  loadModels();
  refreshDashboard();
  loadJsonData();
  renderToolboxMatrix();
});

function initVoice() {
  voice = new VoiceController({
    lang: 'vi-VN',
    autoSpeak: true,
    onStatusChange: (status, label) => {
      const statusEl = document.getElementById("voice-status-text");
      const micBtn = document.getElementById("mic-btn-main");
      const chatMicBtn = document.getElementById("chat-mic-btn");
      const input = document.getElementById("chat-input");

      if (statusEl) {
        statusEl.innerHTML = `<strong>${label}</strong><span>${status === 'recording' ? '🔴 Đang nghe tiếng Việt... Bấm lại mic hoặc thả ra để gửi' : 'Nhấn một lần (hoặc nhấn giữ) Micro để ra lệnh bằng giọng nói'}</span>`;
      }

      if (status === 'recording') {
        if (micBtn) micBtn.classList.add("recording");
        if (chatMicBtn) chatMicBtn.classList.add("recording");
        if (input) input.placeholder = "🔴 Đang nghe bạn nói... (Nói xong bấm lại Micro để gửi)";
      } else {
        if (micBtn) micBtn.classList.remove("recording");
        if (chatMicBtn) chatMicBtn.classList.remove("recording");
        if (input) input.placeholder = "Nhấn Micro 🎙️ để nói hoặc nhập yêu cầu...";
      }
    },
    onInterim: (text) => {
      const input = document.getElementById("chat-input");
      if (input) input.value = text;
    },
    onTranscript: (text) => {
      const input = document.getElementById("chat-input");
      if (input) input.value = text;
      handleSendMessage(text);
    }
  });

  // Attach Click-to-talk & Push-to-talk to both buttons
  const bindMicControl = (btn) => {
    if (!btn) return;
    let holdTimer = null;
    let isHolding = false;

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      if (!isHolding) {
        voice.toggleListening();
      }
    });

    btn.addEventListener("mousedown", () => {
      isHolding = false;
      holdTimer = setTimeout(() => {
        isHolding = true;
        if (!voice.isRecording) voice.startListening();
      }, 300);
    });

    btn.addEventListener("mouseup", () => {
      clearTimeout(holdTimer);
      if (isHolding) {
        voice.stopListening();
        isHolding = false;
      }
    });

    btn.addEventListener("mouseleave", () => {
      clearTimeout(holdTimer);
      if (isHolding) {
        voice.stopListening();
        isHolding = false;
      }
    });

    btn.addEventListener("touchstart", () => {
      isHolding = false;
      holdTimer = setTimeout(() => {
        isHolding = true;
        if (!voice.isRecording) voice.startListening();
      }, 300);
    }, { passive: true });

    btn.addEventListener("touchend", () => {
      clearTimeout(holdTimer);
      if (isHolding) {
        voice.stopListening();
        isHolding = false;
      }
    });
  };

  bindMicControl(document.getElementById("mic-btn-main"));
  bindMicControl(document.getElementById("chat-mic-btn"));

  const toggleVoiceBtn = document.getElementById("toggle-speak-btn");
  if (toggleVoiceBtn) {
    toggleVoiceBtn.addEventListener("click", () => {
      const active = voice.toggleAutoSpeak();
      toggleVoiceBtn.classList.toggle("active", active);
      toggleVoiceBtn.innerHTML = active ? `🔊 Đọc phản hồi: BẬT` : `🔇 Đọc phản hồi: TẮT`;
    });
  }

  const langSelect = document.getElementById("voice-lang-select");
  if (langSelect) {
    langSelect.addEventListener("change", (e) => {
      voice.setLang(e.target.value);
    });
  }
}

function initEventListeners() {
  // Chat form submit
  const sendBtn = document.getElementById("send-btn");
  const chatInput = document.getElementById("chat-input");

  if (sendBtn && chatInput) {
    sendBtn.addEventListener("click", () => {
      const text = chatInput.value.trim();
      if (text) {
        handleSendMessage(text);
        chatInput.value = "";
      }
    });

    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const text = chatInput.value.trim();
        if (text) {
          handleSendMessage(text);
          chatInput.value = "";
        }
      }
    });
  }

  // Quick prompt pills
  document.querySelectorAll(".prompt-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const prompt = pill.getAttribute("data-prompt") || pill.textContent.trim();
      handleSendMessage(prompt);
    });
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(`tab-${tabId}`);
      if (target) target.classList.add("active");

      if (tabId === "json") loadJsonData();
    });
  });

  // Model selector change
  const modelSelect = document.getElementById("ollama-model-select");
  if (modelSelect) {
    modelSelect.addEventListener("change", async (e) => {
      try {
        const res = await fetch(`${API_BASE}/api/models/select", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model: e.target.value })
        });
        const data = await res.json();
        console.log("Active model set to:", data.active_model);
      } catch (err) {
        console.error("Failed to set model:", err);
      }
    });
  }

  // Reset DB button
  const resetBtn = document.getElementById("btn-reset-db");
  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      if (confirm("Bạn có chắc chắn muốn đặt lại cơ sở dữ liệu JSON về mặc định?")) {
        await fetch(`${API_BASE}/api/data/reset", { method: "POST" });
        await refreshDashboard();
        await loadJsonData();
        appendAssistantMessage({
          reply: "⚡ **[Hệ thống]** Đã đặt lại cơ sở dữ liệu `onis_db.json` về trạng thái ban đầu thành công.",
          path: "fast_path",
          sys1: { intent: "system.reset", confidence: 1.0, latency_ms: 2.0 }
        });
      }
    });
  }

  // Reload JSON button
  const reloadJsonBtn = document.getElementById("btn-reload-json");
  if (reloadJsonBtn) {
    reloadJsonBtn.addEventListener("click", loadJsonData);
  }

  // Add Transaction button
  const addTxBtn = document.getElementById("btn-add-tx");
  if (addTxBtn) {
    addTxBtn.addEventListener("click", async () => {
      const type = document.getElementById("tx-input-type").value;
      const amount = parseFloat(document.getElementById("tx-input-amount").value);
      const desc = document.getElementById("tx-input-desc").value.trim();
      const category = document.getElementById("tx-input-cat").value.trim() || (type === "expense" ? "Khác" : "Thu nhập");
      if (!amount || amount <= 0 || !desc) {
        alert("Vui lòng nhập số tiền và mô tả giao dịch hợp lệ!");
        return;
      }
      await fetch(`${API_BASE}/api/finance/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, amount, category, description: desc })
      });
      document.getElementById("tx-input-amount").value = "";
      document.getElementById("tx-input-desc").value = "";
      refreshDashboard();
    });
  }

  // Add Task button
  const addTaskBtn = document.getElementById("btn-add-task");
  if (addTaskBtn) {
    addTaskBtn.addEventListener("click", async () => {
      const title = document.getElementById("task-input-title").value.trim();
      const deadline = document.getElementById("task-input-deadline").value.trim();
      const priority = document.getElementById("task-input-priority").value;
      if (!title) {
        alert("Vui lòng nhập tên công việc!");
        return;
      }
      await fetch(`${API_BASE}/api/tasks/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, deadline: deadline || null, priority })
      });
      document.getElementById("task-input-title").value = "";
      document.getElementById("task-input-deadline").value = "";
      refreshDashboard();
    });
  }

  // Add Savings Goal button
  const addGoalBtn = document.getElementById("btn-add-goal");
  if (addGoalBtn) {
    addGoalBtn.addEventListener("click", async () => {
      const name = document.getElementById("goal-input-name").value.trim();
      const targetAmount = parseFloat(document.getElementById("goal-input-amount").value);
      const deadline = document.getElementById("goal-input-deadline").value;
      if (!name || !targetAmount || targetAmount <= 0) {
        alert("Vui lòng nhập tên mục tiêu và số tiền tiết kiệm hợp lệ!");
        return;
      }
      await fetch(`${API_BASE}/api/savings/goals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, target_amount: targetAmount, deadline: deadline || null })
      });
      document.getElementById("goal-input-name").value = "";
      document.getElementById("goal-input-amount").value = "";
      refreshDashboard();
    });
  }

  // Add Reminder button
  const addRemBtn = document.getElementById("btn-add-rem");
  if (addRemBtn) {
    addRemBtn.addEventListener("click", async () => {
      const text = document.getElementById("rem-input-text").value.trim();
      const time = document.getElementById("rem-input-time").value.trim();
      if (!text) {
        alert("Vui lòng nhập nội dung lời nhắc!");
        return;
      }
      await fetch(`${API_BASE}/api/reminders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, remind_at: time || null })
      });
      document.getElementById("rem-input-text").value = "";
      document.getElementById("rem-input-time").value = "";
      refreshDashboard();
    });
  }

  // Add Note button
  const addNoteBtn = document.getElementById("btn-add-note");
  if (addNoteBtn) {
    addNoteBtn.addEventListener("click", async () => {
      const content = document.getElementById("note-input-content").value.trim();
      const category = document.getElementById("note-input-cat").value;
      if (!content) {
        alert("Vui lòng nhập thông tin cần ghi nhớ!");
        return;
      }
      await fetch(`${API_BASE}/api/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, category })
      });
      document.getElementById("note-input-content").value = "";
      refreshDashboard();
    });
  }

  // Loan Calculator button
  const calcLoanBtn = document.getElementById("btn-calc-loan");
  if (calcLoanBtn) {
    calcLoanBtn.addEventListener("click", calculateLoanDirect);
  }
}

async function loadModels() {
  try {
    const res = await fetch(`${API_BASE}/api/models");
    const data = await res.json();
    const select = document.getElementById("ollama-model-select");
    if (select && data.llm && data.llm.available) {
      select.innerHTML = "";
      data.llm.available.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = `LLM: ${m}`;
        if (m === data.llm.active) opt.selected = true;
        select.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("Failed to load models:", e);
  }
}

async function handleSendMessage(text) {
  if (!text) return;
  appendUserMessage(text);

  // Show thinking indicator
  const thinkingId = appendThinkingMessage();

  try {
    const res = await fetch(`${API_BASE}/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    const data = await res.json();
    removeMessage(thinkingId);

    appendAssistantMessage(data);

    // Speak response
    if (voice && data.reply) {
      voice.speak(data.reply);
    }

    // Refresh state
    if (data.db_summary) {
      if (data.db_summary.finance) renderFinanceSummary(data.db_summary.finance);
      if (data.db_summary.tasks) renderTasks(data.db_summary.tasks);
      if (data.db_summary.savings) renderSavingsGoals(data.db_summary.savings.goals || data.db_summary.savings);
      if (data.db_summary.reminders) renderReminders(data.db_summary.reminders.reminders || data.db_summary.reminders);
      if (data.db_summary.notes) renderNotes(data.db_summary.notes.notes || data.db_summary.notes);
    } else {
      refreshDashboard();
    }

    // Update telemetry
    updateTelemetry(data);

  } catch (err) {
    removeMessage(thinkingId);
    appendAssistantMessage({
      reply: `❌ Đã xảy ra lỗi kết nối: ${err.message}`,
      path: "error"
    });
  }
}

function appendUserMessage(text) {
  const container = document.getElementById("messages-container");
  const msgEl = document.createElement("div");
  msgEl.className = "message user";
  msgEl.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function appendThinkingMessage() {
  const container = document.getElementById("messages-container");
  const id = `thinking_${Date.now()}`;
  const msgEl = document.createElement("div");
  msgEl.id = id;
  msgEl.className = "message assistant";
  msgEl.innerHTML = `
    <div class="bubble" style="color: var(--muted); display: flex; align-items: center; gap: 8px;">
      <div class="dot pulse"></div>
      <span>Kev System 1 đang phân tích định tuyến...</span>
    </div>
  `;
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendAssistantMessage(data) {
  const container = document.getElementById("messages-container");
  const msgEl = document.createElement("div");
  msgEl.className = "message assistant";

  const isFast = data.path === "fast_path";
  const badgeClass = isFast ? "fast" : "reasoning";
  const badgeLabel = isFast 
    ? `⚡ Fast Path (System 1 Kev · ${data.sys1 ? data.sys1.latency_ms : '8'}ms)`
    : `🧠 Reasoning Path (${data.llm ? data.llm.model : 'Ollama LLM'} · ${data.llm ? data.llm.latency_ms : '400'}ms)`;

  const confText = data.sys1 ? `Confidence: ${(data.sys1.confidence * 100).toFixed(1)}%` : "";
  const formattedReply = renderMarkdown(data.reply || "");

  msgEl.innerHTML = `
    <div class="routing-badge ${badgeClass}">${badgeLabel}</div>
    <div class="bubble">
      ${formattedReply}
      <div class="meta-info">
        <span>${confText}</span>
        <button class="btn-speak" title="Nghe lại" onclick="replayAudio('${encodeURIComponent(data.reply || '')}')">🔊 Nghe lại</button>
      </div>
    </div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

window.replayAudio = function(encodedText) {
  const text = decodeURIComponent(encodedText);
  if (voice) voice.speak(text, true);
};

function renderMarkdown(md) {
  let html = escapeHtml(md);
  // bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // inline code
  html = html.replace(/`([^`]+)`/g, '<code style="background: #203553; padding: 2px 6px; border-radius: 4px; color: #72e3dc;">$1</code>');
  // bullet points
  html = html.replace(/^• (.*)$/gm, '<li style="margin-left: 20px; color: var(--muted);">$1</li>');
  // newlines to br
  html = html.replace(/\n\n/g, '<p style="margin: 8px 0;"></p>').replace(/\n/g, '<br>');
  return html;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function refreshDashboard() {
  try {
    const finRes = await fetch(`${API_BASE}/api/finance/summary");
    const finData = await finRes.json();
    if (finData.success) renderFinanceSummary(finData.data);

    const txRes = await fetch(`${API_BASE}/api/finance/transactions");
    const txData = await txRes.json();
    if (txData.success) renderTransactions(txData.transactions);

    const taskRes = await fetch(`${API_BASE}/api/tasks");
    const taskData = await taskRes.json();
    if (taskData.success) renderTasks(taskData);

    const savRes = await fetch(`${API_BASE}/api/savings/goals");
    const savData = await savRes.json();
    if (savData.success) renderSavingsGoals(savData.goals);

    const remRes = await fetch(`${API_BASE}/api/reminders");
    const remData = await remRes.json();
    if (remData.success) renderReminders(remData.reminders);

    const noteRes = await fetch(`${API_BASE}/api/notes");
    const noteData = await noteRes.json();
    if (noteData.success) renderNotes(noteData.notes);
  } catch (err) {
    console.error("Dashboard refresh error:", err);
  }
}

function renderFinanceSummary(data) {
  if (!data) return;
  const balanceEl = document.getElementById("stat-balance");
  const incomeEl = document.getElementById("stat-income");
  const expenseEl = document.getElementById("stat-expense");
  const budgetTextEl = document.getElementById("budget-text");
  const progressFillEl = document.getElementById("budget-progress-fill");

  if (balanceEl) balanceEl.textContent = `${Number(data.balance).toLocaleString()} đ`;
  if (incomeEl) incomeEl.textContent = `${Number(data.total_income).toLocaleString()} đ`;
  if (expenseEl) expenseEl.textContent = `${Number(data.total_expense).toLocaleString()} đ`;

  if (budgetTextEl) {
    budgetTextEl.textContent = `${Number(data.total_expense).toLocaleString()} đ / ${Number(data.monthly_limit).toLocaleString()} đ (${data.percent_budget}%)`;
  }

  if (progressFillEl) {
    const pct = Math.min(data.percent_budget, 100);
    progressFillEl.style.width = `${pct}%`;
    if (pct >= 80) progressFillEl.classList.add("warning");
    else progressFillEl.classList.remove("warning");
  }
}

function renderTransactions(txs) {
  const listEl = document.getElementById("transactions-list");
  if (!listEl || !txs) return;

  if (txs.length === 0) {
    listEl.innerHTML = `<div style="color: var(--muted); text-align: center; padding: 20px;">Chưa có giao dịch nào</div>`;
    return;
  }

  listEl.innerHTML = txs.map(t => {
    const isExp = t.type === "expense";
    const sign = isExp ? "-" : "+";
    const amtClass = isExp ? "expense" : "income";
    return `
      <div class="item-row">
        <div class="item-left">
          <div style="font-size: 1.2rem;">${isExp ? '💸' : '💰'}</div>
          <div class="item-desc">
            <strong>${escapeHtml(t.description)}</strong>
            <small>${escapeHtml(t.category)} · ${t.date ? t.date.replace('T', ' ') : ''}</small>
          </div>
        </div>
        <div class="item-right">
          <span class="amount ${amtClass}">${sign}${Number(t.amount).toLocaleString()} đ</span>
          <button class="btn-del" title="Xóa giao dịch" onclick="deleteTransaction('${t.id}')">🗑️</button>
        </div>
      </div>
    `;
  }).join("");
}

window.deleteTransaction = async function(id) {
  if (confirm("Xác nhận xóa giao dịch này?")) {
    await fetch(`${API_BASE}/api/finance/${id}`, { method: "DELETE" });
    refreshDashboard();
  }
};

function renderTasks(data) {
  const listEl = document.getElementById("tasks-list");
  const pendingStat = document.getElementById("stat-pending-tasks");
  const completedStat = document.getElementById("stat-completed-tasks");

  if (pendingStat) pendingStat.textContent = data.pending_count || 0;
  if (completedStat) completedStat.textContent = data.completed_count || 0;

  if (!listEl || !data.tasks) return;

  if (data.tasks.length === 0) {
    listEl.innerHTML = `<div style="color: var(--muted); text-align: center; padding: 20px;">Chưa có nhiệm vụ nào</div>`;
    return;
  }

  listEl.innerHTML = data.tasks.map(t => {
    const isDone = t.status === "completed";
    return `
      <div class="task-row ${isDone ? 'completed' : ''}" onclick="toggleTask('${t.id}')">
        <div style="display: flex; align-items: center; gap: 12px;">
          <input type="checkbox" class="task-checkbox" ${isDone ? 'checked' : ''} onclick="event.stopPropagation(); toggleTask('${t.id}')">
          <div class="task-text">
            <strong>${escapeHtml(t.title)}</strong>
            ${t.deadline ? `<br><small style="color: var(--muted);">⏰ Hạn: ${t.deadline.replace('T', ' ')}</small>` : ''}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="badge-priority ${t.priority}">${t.priority}</span>
          <button class="btn-del" title="Xóa task" onclick="event.stopPropagation(); deleteTask('${t.id}')">🗑️</button>
        </div>
      </div>
    `;
  }).join("");
}

window.toggleTask = async function(id) {
  await fetch(`${API_BASE}/api/tasks/toggle/${id}`, { method: "POST" });
  refreshDashboard();
};

window.deleteTask = async function(id) {
  if (confirm("Xác nhận xóa nhiệm vụ này?")) {
    await fetch(`${API_BASE}/api/tasks/${id}`, { method: "DELETE" });
    refreshDashboard();
  }
};

function renderSavingsGoals(goals) {
  const gridEl = document.getElementById("savings-goals-grid");
  const totalStat = document.getElementById("stat-savings-total");
  const compStat = document.getElementById("stat-savings-completed");
  const pctStat = document.getElementById("stat-savings-pct");

  if (!goals) return;

  const totalSaved = goals.reduce((acc, g) => acc + (g.current_amount || 0), 0);
  const completedCount = goals.filter(g => g.current_amount >= g.target_amount).length;
  const avgPct = goals.length > 0
    ? (goals.reduce((acc, g) => acc + (g.current_amount / (g.target_amount || 1)), 0) / goals.length * 100)
    : 0;

  if (totalStat) totalStat.textContent = `${Number(totalSaved).toLocaleString()} đ`;
  if (compStat) compStat.textContent = `${completedCount} / ${goals.length}`;
  if (pctStat) pctStat.textContent = `${avgPct.toFixed(1)}%`;

  if (!gridEl) return;
  if (goals.length === 0) {
    gridEl.innerHTML = `<div style="color: var(--muted); padding: 20px;">Chưa có mục tiêu tiết kiệm nào</div>`;
    return;
  }

  gridEl.innerHTML = goals.map(g => {
    const pct = Math.min(100, Math.round((g.current_amount / g.target_amount) * 100));
    return `
      <div class="goal-card">
        <div class="goal-header">
          <div>
            <div class="goal-title">🎯 ${escapeHtml(g.name)}</div>
            ${g.deadline ? `<small style="color: var(--muted);">⏰ Hạn chót: ${g.deadline}</small>` : ''}
          </div>
          <button class="btn-del" title="Xóa mục tiêu" onclick="deleteGoal('${g.id}')">🗑️</button>
        </div>
        <div class="goal-amounts">
          <span>Đã có: <strong style="color: var(--cyan);">${Number(g.current_amount).toLocaleString()} đ</strong></span>
          <span>Mục tiêu: ${Number(g.target_amount).toLocaleString()} đ (${pct}%)</span>
        </div>
        <div class="goal-track">
          <div class="goal-fill" style="width: ${pct}%;"></div>
        </div>
        <div class="goal-actions">
          <button class="btn-action primary" onclick="depositGoal('${g.id}', '${escapeHtml(g.name)}')">💰 Nạp thêm tiền</button>
        </div>
      </div>
    `;
  }).join("");
}

window.depositGoal = async function(id, name) {
  const amtStr = prompt(`Nhập số tiền muốn nạp vào quỹ "${name}" (VNĐ):`, "1000000");
  if (!amtStr) return;
  const amount = parseFloat(amtStr.replace(/[,.]/g, ""));
  if (amount && amount > 0) {
    await fetch(`${API_BASE}/api/savings/deposit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal_id: id, amount })
    });
    refreshDashboard();
  }
};

window.deleteGoal = async function(id) {
  if (confirm("Xác nhận xóa mục tiêu tiết kiệm này?")) {
    await fetch(`${API_BASE}/api/savings/goals/${id}`, { method: "DELETE" });
    refreshDashboard();
  }
};

function renderReminders(rems) {
  const listEl = document.getElementById("reminders-list");
  if (!listEl || !rems) return;
  if (rems.length === 0) {
    listEl.innerHTML = `<div style="color: var(--muted); padding: 14px;">Chưa có lời nhắc nào</div>`;
    return;
  }
  listEl.innerHTML = rems.map(r => `
    <div class="note-item">
      <div>
        <div style="font-weight: 600; color: var(--text);">⏰ ${escapeHtml(r.text)}</div>
        ${r.remind_at ? `<small style="color: var(--muted);">Thời gian: ${r.remind_at.replace('T', ' ')}</small>` : ''}
      </div>
      <button class="btn-del" title="Xóa lời nhắc" onclick="deleteReminder('${r.id}')">🗑️</button>
    </div>
  `).join("");
}

window.deleteReminder = async function(id) {
  await fetch(`${API_BASE}/api/reminders/${id}`, { method: "DELETE" });
  refreshDashboard();
};

function renderNotes(notes) {
  const listEl = document.getElementById("notes-list");
  if (!listEl || !notes) return;
  if (notes.length === 0) {
    listEl.innerHTML = `<div style="color: var(--muted); padding: 14px;">Chưa có ghi nhớ nào</div>`;
    return;
  }
  listEl.innerHTML = notes.map(n => `
    <div class="note-item">
      <div>
        <div style="color: var(--text); font-size: 0.9rem;">📌 ${escapeHtml(n.content)}</div>
        <small style="color: var(--muted);">${n.created_at ? n.created_at.slice(0, 10) : ''}</small>
      </div>
      <span class="note-badge">${escapeHtml(n.category || 'general')}</span>
    </div>
  `).join("");
}

async function calculateLoanDirect() {
  const principal = parseFloat(document.getElementById("calc-principal").value) || 50000000;
  const rate = parseFloat(document.getElementById("calc-rate").value) || 10.5;
  const months = parseInt(document.getElementById("calc-months").value) || 12;

  try {
    const res = await fetch(`${API_BASE}/api/finance/loan/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ principal, annual_rate_pct: rate, months })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById("calc-res-monthly").textContent = `${Number(data.monthly_payment).toLocaleString()} đ`;
      document.getElementById("calc-res-interest").textContent = `${Number(data.total_interest).toLocaleString()} đ`;
      document.getElementById("calc-res-total").textContent = `${Number(data.total_payment).toLocaleString()} đ`;
    }
  } catch (err) {
    console.error("Loan calculation error:", err);
  }
}

const ALL_TOOLS = [
  {
    group: "💰 Tài chính",
    name: "create_expense",
    desc: "Ghi nhận khoản chi tiêu kèm danh mục và số tiền",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Chi 45k tiền cà phê sáng"
  },
  {
    group: "💰 Tài chính",
    name: "create_income",
    desc: "Ghi nhận nguồn thu nhập (lương, thưởng, bán đồ...)",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Nhận lương tháng 25 triệu đồng"
  },
  {
    group: "💰 Tài chính",
    name: "get_summary",
    desc: "Xem tổng quan số dư khả dụng, tổng thu và tổng chi",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Xem tổng quan tài chính và số dư hiện tại"
  },
  {
    group: "💰 Tài chính",
    name: "get_transactions",
    desc: "Truy xuất danh sách các giao dịch gần đây",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Cho tôi xem 5 giao dịch gần nhất"
  },
  {
    group: "💰 Tài chính",
    name: "set_monthly_budget",
    desc: "Thiết lập hoặc cập nhật hạn mức chi tiêu trong tháng",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Đặt hạn mức ngân sách tháng 12 triệu"
  },
  {
    group: "💰 Tài chính",
    name: "calculate_loan",
    desc: "Máy tính tiền trả góp & tổng tiền lãi vay ngân hàng",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Tính trả góp vay 40 triệu trong 12 tháng lãi 9%"
  },
  {
    group: "💰 Tài chính",
    name: "delete_transaction",
    desc: "Xóa bản ghi giao dịch nhầm lẫn khỏi sổ thu chi",
    path: "fast",
    ui: true,
    voice: false,
    testPrompt: "Xóa giao dịch"
  },
  {
    group: "📝 Công việc",
    name: "create_task",
    desc: "Tạo nhiệm vụ công việc có mốc hạn chót và mức ưu tiên",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Thêm task chuẩn bị tài liệu dự án trước 17h thứ 6 gấp"
  },
  {
    group: "📝 Công việc",
    name: "complete_task",
    desc: "Đánh dấu hoàn thành nhiệm vụ theo tên hoặc từ khóa",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Hoàn thành task Nộp báo cáo tài chính"
  },
  {
    group: "📝 Công việc",
    name: "delete_task",
    desc: "Xóa nhiệm vụ khỏi danh sách công việc",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Xóa task Học Kotlin"
  },
  {
    group: "📝 Công việc",
    name: "get_tasks",
    desc: "Tra cứu danh sách công việc đang chờ và đã hoàn thành",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Có những nhiệm vụ nào cần làm hôm nay?"
  },
  {
    group: "🎯 Tiết kiệm",
    name: "add_goal",
    desc: "Thiết lập mục tiêu tích lũy tài chính có kỳ hạn",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Tạo mục tiêu tiết kiệm 50 triệu mua xe máy mới"
  },
  {
    group: "🎯 Tiết kiệm",
    name: "deposit",
    desc: "Nạp thêm tiền vào quỹ mục tiêu tiết kiệm",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Nạp 3 triệu vào quỹ Laptop"
  },
  {
    group: "🎯 Tiết kiệm",
    name: "get_goals",
    desc: "Xem danh sách các mục tiêu tiết kiệm và tỷ lệ hoàn thành",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Tiến độ các mục tiêu tiết kiệm thế nào?"
  },
  {
    group: "🎯 Tiết kiệm",
    name: "delete_goal",
    desc: "Xóa mục tiêu tiết kiệm",
    path: "fast",
    ui: true,
    voice: false,
    testPrompt: "Xóa mục tiêu tiết kiệm"
  },
  {
    group: "⏰ Lời nhắc",
    name: "create_reminder",
    desc: "Thiết lập lời nhắc nhở thời gian cụ thể",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Nhắc tôi gọi điện cho khách hàng lúc 14h chiều mai"
  },
  {
    group: "⏰ Lời nhắc",
    name: "get_reminders",
    desc: "Xem danh sách các lịch hẹn và lời nhắc đang chờ",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Xem các lời nhắc nhở của tôi"
  },
  {
    group: "⏰ Lời nhắc",
    name: "delete_reminder",
    desc: "Xóa hoặc hủy lời nhắc nhở",
    path: "fast",
    ui: true,
    voice: false,
    testPrompt: "Xóa lời nhắc"
  },
  {
    group: "🧠 Bộ nhớ",
    name: "save_note",
    desc: "Lưu thói quen, sở thích, quy tắc cá nhân vào bộ nhớ dài hạn",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Ghi nhớ: Ưu tiên mua sắm vào cuối tuần để nhận voucher"
  },
  {
    group: "🧠 Bộ nhớ",
    name: "get_notes",
    desc: "Truy xuất danh sách ghi nhớ cá nhân của người dùng",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Tôi đã lưu những ghi nhớ nào?"
  },
  {
    group: "🛡️ An toàn",
    name: "validate_transaction",
    desc: "Kiểm tra giới hạn số tiền, ngăn chặn lỗi và thao tác nguy hiểm",
    path: "fast",
    ui: true,
    voice: true,
    testPrompt: "Chi 2 tỷ mua biệt thự"
  },
  {
    group: "🧠 Suy luận",
    name: "explain_finances",
    desc: "Phân tích xu hướng chi tiêu sâu, đối chiếu ngân sách & đưa khuyến nghị",
    path: "reasoning",
    ui: true,
    voice: true,
    testPrompt: "Vì sao tháng này tôi tiêu nhiều tiền hơn bình thường?"
  },
  {
    group: "🧠 Suy luận",
    name: "plan_schedule",
    desc: "Lập lịch trình và sắp xếp thứ tự ưu tiên tối ưu cho các công việc",
    path: "reasoning",
    ui: true,
    voice: true,
    testPrompt: "Lập kế hoạch công việc hôm nay giúp tôi dựa trên các task"
  }
];

function renderToolboxMatrix() {
  const tbody = document.getElementById("toolbox-matrix-body");
  if (!tbody) return;

  tbody.innerHTML = ALL_TOOLS.map(t => {
    const isFast = t.path === "fast";
    const pathBadge = isFast
      ? `<span class="badge-fast">⚡ Fast Path (~10ms)</span>`
      : `<span class="badge-reason">🧠 Reasoning Path (LLM)</span>`;

    const uiBadge = t.ui
      ? `<span class="badge-ui">🖱️ Có Form/Nút UI</span>`
      : `<span style="color: var(--muted); font-size: 0.75rem;">—</span>`;

    const voiceBadge = t.voice
      ? `<span class="badge-voice">🎙️ Voice & Chat</span>`
      : `<span style="color: var(--muted); font-size: 0.75rem;">—</span>`;

    return `
      <tr>
        <td><strong>${escapeHtml(t.group)}</strong></td>
        <td><code>${escapeHtml(t.name)}</code></td>
        <td>${escapeHtml(t.desc)}</td>
        <td>${pathBadge}</td>
        <td>${uiBadge}</td>
        <td>${voiceBadge}</td>
        <td>
          <button class="btn-action" style="padding: 3px 8px; font-size: 0.75rem;" onclick="testRunTool('${encodeURIComponent(t.testPrompt)}')">
            ▶ Chạy thử
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

window.testRunTool = function(encodedPrompt) {
  const prompt = decodeURIComponent(encodedPrompt);
  const input = document.getElementById("chat-input");
  if (input) input.value = prompt;
  handleSendMessage(prompt);
};

function updateTelemetry(data) {
  if (data.path === "fast_path") {
    fastPathCount++;
    savedTokensCount += 350; // Average tokens saved by avoiding LLM
  } else if (data.path === "reasoning_path") {
    reasoningCount++;
  }

  const fastCountEl = document.getElementById("telem-fast-count");
  const reasonCountEl = document.getElementById("telem-reason-count");
  const tokensSavedEl = document.getElementById("telem-tokens-saved");

  if (fastCountEl) fastCountEl.textContent = fastPathCount;
  if (reasonCountEl) reasonCountEl.textContent = reasoningCount;
  if (tokensSavedEl) tokensSavedEl.textContent = `${savedTokensCount.toLocaleString()} tokens`;

  if (!data.sys1) return;

  const sys1 = data.sys1;
  const lastIntentEl = document.getElementById("telem-last-intent");
  const lastConfEl = document.getElementById("telem-last-conf");
  const lastCompEl = document.getElementById("telem-last-comp");
  const lastRiskEl = document.getElementById("telem-last-risk");
  const lastLatencyEl = document.getElementById("telem-last-latency");

  if (lastIntentEl) lastIntentEl.textContent = sys1.intent;
  if (lastConfEl) lastConfEl.textContent = `${(sys1.confidence * 100).toFixed(1)}%`;
  if (lastCompEl) lastCompEl.textContent = sys1.complexity;
  if (lastRiskEl) lastRiskEl.textContent = sys1.risk;
  if (lastLatencyEl) lastLatencyEl.textContent = `${sys1.latency_ms} ms (Fast Path)`;

  // Render probability bars
  const probContainer = document.getElementById("telem-probs-bars");
  if (probContainer && sys1.probabilities) {
    const sorted = Object.entries(sys1.probabilities).sort((a, b) => b[1] - a[1]);
    probContainer.innerHTML = sorted.slice(0, 6).map(([k, v]) => `
      <div class="prob-bar-row">
        <span class="prob-bar-label" title="${k}">${k}</span>
        <div class="prob-bar-track">
          <div class="prob-bar-fill" style="width: ${(v * 100).toFixed(1)}%;"></div>
        </div>
        <span class="prob-val">${(v * 100).toFixed(0)}%</span>
      </div>
    `).join("");
  }
}

async function loadJsonData() {
  const jsonBox = document.getElementById("json-viewer-box");
  if (!jsonBox) return;
  try {
    const res = await fetch(`${API_BASE}/api/data");
    const data = await res.json();
    jsonBox.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    jsonBox.textContent = `Lỗi tải JSON: ${err.message}`;
  }
}
