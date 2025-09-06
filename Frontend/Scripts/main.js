import { handleProcessEmail, refreshData, handleLoadSample, handleRegenerateResponse } from "./events.js";
import { getEmails } from "./api.js";

console.log("🚀 Starting AI Email Assistant...");

document.addEventListener("DOMContentLoaded", async () => {
  console.log("📄 DOM loaded, setting up...");
  
  // Setup button handlers
  const buttons = {
    btnProcessEmail: handleProcessEmail,
    btnRefresh: refreshData,
    btnSample: handleLoadSample,
    btnRegenerateAll: async () => {
      console.log("🔄 Regenerating all responses...");
      try {
        const emails = await getEmails();
        for (const email of emails) {
          if (email.status !== 'resolved') {
            await handleRegenerateResponse(email.id);
          }
        }
      } catch (error) {
        console.error("❌ Regenerate all failed:", error);
      }
    }
  };

  // Attach event listeners
  Object.entries(buttons).forEach(([id, handler]) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.onclick = handler;
      console.log(`✅ Handler attached to ${id}`);
    } else {
      console.warn(`⚠️ Button ${id} not found`);
    }
  });

  // Initial load
  console.log("🔄 Loading initial data...");
  await refreshData();
  
  // Auto-refresh every 30 seconds
  setInterval(refreshData, 30000);
  
  console.log("🎉 Setup complete!");
});