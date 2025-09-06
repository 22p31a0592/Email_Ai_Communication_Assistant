let chart = null;

export function updateConnectionStatus(connected) {
  const el = document.getElementById("connectionStatus");
  if (!el) return;
  
  el.className = connected ? "connection-status status-connected" : "connection-status status-disconnected";
  el.innerHTML = connected ? "🟢 Connected to AI Backend" : "🔴 Backend Disconnected";
}

export function showNotification(msg, type = "success") {
  console.log(`📢 ${type.toUpperCase()}: ${msg}`);
  
  const note = document.createElement("div");
  note.className = `notification ${type}`;
  note.textContent = msg;
  note.style.cssText = `
    position: fixed; top: 20px; right: 20px; padding: 15px 20px;
    border-radius: 6px; color: white; font-weight: bold; z-index: 9999;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 350px;
    opacity: 0; transform: translateX(100%); transition: all 0.3s ease;
  `;
  
  const colors = {
    success: "#27ae60", error: "#e74c3c", info: "#3498db", warning: "#f39c12"
  };
  note.style.backgroundColor = colors[type] || colors.success;
  
  document.body.appendChild(note);
  
  setTimeout(() => {
    note.style.opacity = "1";
    note.style.transform = "translateX(0)";
  }, 100);
  
  setTimeout(() => {
    note.style.opacity = "0";
    note.style.transform = "translateX(100%)";
    setTimeout(() => note.remove(), 300);
  }, 4000);
}

export function renderEmails(emails, handlers) {
  console.log("🎨 RENDERING EMAILS");
  console.log("📧 Emails count:", emails?.length || 0);
  console.log("🔧 Handlers:", {
    send: typeof handlers?.send,
    regenerate: typeof handlers?.regenerate
  });

  const container = document.getElementById("emailContainer");
  if (!container) {
    console.error("❌ emailContainer element not found!");
    return;
  }

  // Clear existing content
  container.innerHTML = '';

  if (!emails || emails.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="text-align: center; padding: 50px; color: #7f8c8d;">
        <h3>📭 No Emails Found</h3>
        <p>Process some emails or load sample data to get started.</p>
      </div>`;
    return;
  }

  if (!handlers?.send || !handlers?.regenerate) {
    console.error("❌ Invalid handlers provided!");
    container.innerHTML = `<div style="color: red; padding: 20px;">Error: Button handlers not configured properly</div>`;
    return;
  }

  // Create email elements
  emails.forEach((email, index) => {
    console.log(`📝 Creating email ${index + 1}:`, email);

    const emailDiv = document.createElement('div');
    emailDiv.className = 'email-item';
    emailDiv.innerHTML = `
      <div class="email-header">
        <div class="email-info">
          <div class="email-sender">📧 ${email.sender || 'Unknown'}</div>
          <div class="email-subject">${email.subject || 'No Subject'}</div>
          <div class="email-date">${email.date_received ? new Date(email.date_received).toLocaleString() : 'Unknown Date'}</div>
        </div>
        <div class="tags">
          <span class="tag ${email.priority || 'normal'}">${(email.priority || 'normal').toUpperCase()}</span>
          <span class="tag ${email.sentiment || 'neutral'}">${(email.sentiment || 'neutral').toUpperCase()}</span>
          <span class="tag ${email.status || 'pending'}">${(email.status || 'pending').toUpperCase()}</span>
        </div>
      </div>
      <div class="email-body">${email.body || 'No content'}</div>
      <div class="extracted-info">
        <h4>🔍 Extracted Info</h4>
        <div><strong>Contact:</strong> ${email.contact_info || 'N/A'}</div>
        <div><strong>Requirements:</strong> ${email.requirements || 'N/A'}</div>
        <div><strong>Keywords:</strong> ${email.keywords || 'N/A'}</div>
      </div>
      <div class="ai-response">
        <h4>🤖 AI-Generated Response</h4>
        <div class="ai-response-text">${email.ai_response || 'No response generated yet'}</div>
        <div class="response-actions">
          <button type="button" class="btn-small send-btn" data-email-id="${email.id}" ${email.status === 'resolved' ? 'disabled' : ''}>
            ${email.status === 'resolved' ? '✅ Sent' : '✉️ Send Response'}
          </button>
          <button type="button" class="btn-small regen-btn" data-email-id="${email.id}">
            🔄 Regenerate
          </button>
        </div>
      </div>
    `;

    container.appendChild(emailDiv);

    // Attach event listeners to the buttons we just created
    const sendBtn = emailDiv.querySelector('.send-btn');
    const regenBtn = emailDiv.querySelector('.regen-btn');

    if (sendBtn && !sendBtn.disabled) {
      sendBtn.addEventListener('click', async function() {
        console.log(`🚀 SEND CLICKED for email ${email.id}`);
        
        this.disabled = true;
        this.textContent = '⏳ Sending...';
        
        try {
          await handlers.send(email.id);
          console.log(`✅ Send completed for ${email.id}`);
        } catch (error) {
          console.error(`❌ Send failed for ${email.id}:`, error);
          this.disabled = false;
          this.textContent = '✉️ Send Response';
        }
      });
    }

    if (regenBtn) {
      regenBtn.addEventListener('click', async function() {
        console.log(`🔄 REGENERATE CLICKED for email ${email.id}`);
        
        this.disabled = true;
        this.textContent = '⏳ Regenerating...';
        
        try {
          await handlers.regenerate(email.id);
          console.log(`✅ Regenerate completed for ${email.id}`);
        } catch (error) {
          console.error(`❌ Regenerate failed for ${email.id}:`, error);
          this.disabled = false;
          this.textContent = '🔄 Regenerate';
        }
      });
    }
  });

  console.log("✅ All emails rendered successfully!");
}

export function updateChart(analytics) {
  const ctx = document.getElementById("emailChart");
  if (!ctx) {
    console.warn("⚠️ Chart canvas not found");
    return;
  }

  try {
    if (chart) chart.destroy();

    const data = {
      total_emails: analytics?.total_emails || 0,
      urgent_emails: analytics?.urgent_emails || 0,
      sentiment_breakdown: analytics?.sentiment_breakdown || {}
    };

    chart = new Chart(ctx.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: ["Urgent", "Normal", "Positive", "Negative", "Neutral"],
        datasets: [{
          data: [
            data.urgent_emails,
            Math.max(0, data.total_emails - data.urgent_emails),
            data.sentiment_breakdown.positive || 0,
            data.sentiment_breakdown.negative || 0,
            data.sentiment_breakdown.neutral || 0
          ],
          backgroundColor: ["#e74c3c", "#3498db", "#27ae60", "#e74c3c", "#f39c12"]
        }]
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        responsive: true
      }
    });
    
    console.log("📊 Chart updated");
  } catch (error) {
    console.error("❌ Chart update failed:", error);
  }
}