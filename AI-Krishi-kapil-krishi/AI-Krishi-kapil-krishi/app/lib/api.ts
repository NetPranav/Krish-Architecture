/**
 * SmartAgri API Client
 * Connects Next.js frontend to the FastAPI backend.
 * Change API_BASE to your ngrok URL when running remotely.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
