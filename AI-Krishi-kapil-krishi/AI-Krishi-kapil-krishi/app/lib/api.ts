/**
 * SmartAgri API Client
 * Connects Next.js frontend to the FastAPI backend.
 * Change API_BASE to your ngrok URL when running remotely.
 */

let API_BASE = "http://localhost:8000";

if (typeof window !== "undefined") {
  // Dynamically point to the same host as the frontend but on port 8000.
  // This automatically uses your Wi-Fi IP (192.168.137.83) on the phone!
  API_BASE = `http://${window.location.hostname}:8000`;
}

// Fallback to explicitly defined env var if available
if (process.env.NEXT_PUBLIC_API_URL) {
  API_BASE = process.env.NEXT_PUBLIC_API_URL;
}
async function apiFetch(path: string, options?: RequestInit) {
  const url = `${API_BASE}${path}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: { ...options?.headers },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || err.detail || res.statusText);
    }
    return await res.json();
  } catch (error: any) {
    if (error.message?.includes("fetch")) {
      console.warn(`API unreachable: ${url} — using fallback`);
      return null;
    }
    throw error;
  }
}

// ── Auth ─────────────────────────────────────────────────────────
export async function login(emailOrPhone: string, password: string) {
  const form = new FormData();
  form.append("email_or_phone", emailOrPhone);
  form.append("password", password);
  return apiFetch("/api/auth/login", { method: "POST", body: form });
}

export async function register(fullName: string, phone: string, language: string, operation: string) {
  const form = new FormData();
  form.append("full_name", fullName);
  form.append("phone", phone);
  form.append("language", language);
  form.append("operation", operation);
  return apiFetch("/api/auth/register", { method: "POST", body: form });
}

// ── Dashboard ────────────────────────────────────────────────────
export async function getDashboard() {
  return apiFetch("/api/dashboard");
}

// ── Profile ──────────────────────────────────────────────────────
export async function getProfile() {
  return apiFetch("/api/profile");
}

export async function updateProfile(data: { land_size?: string, land_unit?: string, soil_type?: string, voice_assistance?: boolean, language?: string }) {
  const form = new FormData();
  if (data.land_size) form.append("land_size", data.land_size);
  if (data.land_unit) form.append("land_unit", data.land_unit);
  if (data.soil_type) form.append("soil_type", data.soil_type);
  if (data.voice_assistance !== undefined) form.append("voice_assistance", String(data.voice_assistance));
  if (data.language) form.append("language", data.language);
  return apiFetch("/api/profile", { method: "PUT", body: form });
}

// ── Weather ──────────────────────────────────────────────────────
export async function getWeatherCurrent(lat = 20.0063, lon = 73.7895) {
  return apiFetch(`/api/weather/current?lat=${lat}&lon=${lon}`);
}

export async function getWeatherForecast(lat = 20.0063, lon = 73.7895) {
  return apiFetch(`/api/weather/forecast?lat=${lat}&lon=${lon}`);
}

// ── Mandi ────────────────────────────────────────────────────────
export async function getMandiPrices(search = "") {
  return apiFetch(`/api/mandi/prices?search=${encodeURIComponent(search)}`);
}

export async function getMandiNearby(sort = "nearest") {
  return apiFetch(`/api/mandi/nearby?sort=${sort}`);
}

export async function getMandiDetail(name: string) {
  return apiFetch(`/api/mandi/detail/${encodeURIComponent(name)}`);
}

export async function getMandiForecast(commodity = "onion") {
  return apiFetch(`/api/mandi/forecast?commodity=${encodeURIComponent(commodity)}`);
}

// ── Products ─────────────────────────────────────────────────────
export async function analyzeProduct(name: string) {
  return apiFetch(`/api/products/analyze?name=${encodeURIComponent(name)}`);
}

// ── Telemetry ────────────────────────────────────────────────────
export async function getTelemetry() {
  return apiFetch("/api/telemetry/live");
}

export async function syncTelemetry() {
  return apiFetch("/api/telemetry/sync", { method: "POST" });
}

// ── Alerts ───────────────────────────────────────────────────────
export async function getAlerts() {
  return apiFetch("/api/alerts");
}

// ── Irrigation ───────────────────────────────────────────────────
export async function getIrrigationStatus() {
  return apiFetch("/api/irrigation/status");
}

export async function controlPump(action: "start" | "stop") {
  const form = new FormData();
  form.append("action", action);
  return apiFetch("/api/irrigation/pump", { method: "POST", body: form });
}

// ── Vision Scanner ───────────────────────────────────────────────
export async function scanLeaf(file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiFetch("/api/vision/scan-leaf", { method: "POST", body: form });
}

// ── Mitra AI Chat ────────────────────────────────────────────────
export async function mitraChat(
  text: string,
  sensors: Record<string, number> = {},
  crop?: string,
  days?: number,
  image?: File
) {
  const defaultSensors = {
    N: 80, P: 45, K: 40,
    temperature: 28, humidity: 65,
    ph: 6.5, rainfall: 120,
  };
  const mergedSensors = { ...defaultSensors, ...sensors };

  const form = new FormData();
  form.append("text", text);
  form.append("sensors", JSON.stringify(mergedSensors));
  if (crop) form.append("crop", crop);
  form.append("days", String(days || 60));
  if (image) form.append("image", image);
  return apiFetch("/api/mitra/chat", { method: "POST", body: form });
}

export async function getMitraHistory(n = 10) {
  return apiFetch(`/api/mitra/history?n=${n}`);
}

export async function getMitraStatus() {
  return apiFetch("/api/mitra/status");
}

// ── Translation (Google Translate API — free tier via proxy) ─────
// Uses the browser-native approach for lightweight translation
export async function translateText(text: string, sourceLang: string, targetLang: string): Promise<string> {
  if (sourceLang === targetLang || !text.trim()) return text;
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
    const res = await fetch(url);
    const data = await res.json();
    // Google returns nested arrays: [[["translated text","original text",...]]]
    return data?.[0]?.map((s: any[]) => s[0]).join('') || text;
  } catch (e) {
    console.warn('Translation failed, using original text:', e);
    return text;
  }
}
