import { processEmail, getEmails, getAnalytics, sendResponse, regenerateResponse, loadSampleData } from "./api.js";
import { updateConnectionStatus, showNotification, renderEmails, updateChart } from "./ui.js";

let emails = [];

export async function refreshData() {
  console.log("🔄 Refreshing data...");
  try {
    emails = await getEmails();
    updateConnectionStatus(true);
    
    renderEmails(emails, { 
      send: handleSendResponse, 
      regenerate: handleRegenerateResponse 
    });
    
    const analytics = await getAnalytics();
    
    document.getElementById("totalEmails").textContent = analytics.total_emails || 0;
    document.getElementById("urgentEmails").textContent = analytics.urgent_emails || 0;
    document.getElementById("resolvedEmails").textContent = analytics.resolved_emails || 0;
    document.getElementById("pendingEmails").textContent = analytics.pending_emails || 0;
    
    updateChart(analytics);
    console.log("✅ Data refresh complete");
    
  } catch (error) {
    console.error("❌ Refresh failed:", error);
    updateConnectionStatus(false);
    showNotification("Backend connection failed: " + error.message, "error");
  }
}

export async function handleProcessEmail() {
  const sender = document.getElementById("emailSender")?.value?.trim();
  const subject = document.getElementById("emailSubject")?.value?.trim();
  const body = document.getElementById("emailBody")?.value?.trim();
  
  if (!sender || !subject || !body) {
    showNotification("Please fill all fields", "error");
    return;
  }

  try {
    showNotification("Processing email...", "info");
    await processEmail({ sender, subject, body });
    
    // Clear form
    document.getElementById("emailSender").value = "";
    document.getElementById("emailSubject").value = "";
    document.getElementById("emailBody").value = "";
    
    showNotification("Email processed successfully!", "success");
    await refreshData();
  } catch (error) {
    console.error("❌ Process email failed:", error);
    showNotification("Failed to process email: " + error.message, "error");
  }
}

export async function handleSendResponse(id) {
  console.log("📤 SEND HANDLER CALLED for ID:", id);
  
  if (!id) {
    showNotification("Invalid email ID", "error");
    return;
  }

  try {
    await sendResponse(id);
    showNotification(`Response sent for email #${id}`, "success");
    await refreshData();
  } catch (error) {
    console.error("❌ Send failed:", error);
    showNotification(`Failed to send response: ${error.message}`, "error");
  }
}

export async function handleRegenerateResponse(id) {
  console.log("🔄 REGENERATE HANDLER CALLED for ID:", id);
  
  if (!id) {
    showNotification("Invalid email ID", "error");
    return;
  }

  try {
    await regenerateResponse(id);
    showNotification(`Response regenerated for email #${id}`, "success");
    await refreshData();
  } catch (error) {
    console.error("❌ Regenerate failed:", error);
    showNotification(`Failed to regenerate response: ${error.message}`, "error");
  }
}

export async function handleLoadSample() {
  try {
    showNotification("Loading sample data...", "info");
    await loadSampleData();
    showNotification("Sample data loaded successfully", "success");
    await refreshData();
  } catch (error) {
    console.error("❌ Load sample failed:", error);
    showNotification("Failed to load sample data: " + error.message, "error");
  }
}
