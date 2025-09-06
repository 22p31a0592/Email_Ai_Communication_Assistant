const API_BASE = "http://127.0.0.1:5000/api";

async function apiCall(endpoint, method = "GET", data = null) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (data) options.body = JSON.stringify(data);

  console.log(`🌐 API Call: ${method} ${API_BASE}${endpoint}`, data);
  
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log(`✅ API Success: ${method} ${endpoint}`, result);
    return result;
  } catch (error) {
    console.error(`❌ API Error: ${method} ${endpoint}`, error);
    throw error;
  }
}

export async function loadSampleData() { return apiCall("/load_sample", "POST"); }
export async function getEmails() { return apiCall("/emails"); }
export async function processEmail(data) { return apiCall("/process_email", "POST", data); }
export async function getAnalytics() { return apiCall("/analytics"); }
export async function sendResponse(id) { return apiCall("/send_response", "POST", { email_id: id }); }
export async function regenerateResponse(id) { return apiCall("/regenerate_response", "POST", { email_id: id }); }
