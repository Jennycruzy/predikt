/**
 * Backend API client for predikt
 * Handles all communication with the FastAPI debate engine.
 */

// Always use the Next.js rewrite proxy path (/api/*).
// In dev: Next.js proxies /api/* → http://localhost:8000/*
// On Vercel: Next.js proxies /api/* → http://VPS_IP:8000/* server-side
//            (no HTTPS/mixed-content issue because the proxy runs on the server)
const API_BASE_URL = "/api";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request(path: string, options?: RequestInit) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `API Error: ${res.status}`);
    }
    return res.json();
  }

  // ── Markets ──────────────────────────────────────
  async createMarket(params: {
    question: string;
    category: string;
    deadline_hours: number;
    num_validators?: number;
    debate_rounds?: number;
  }) {
    return this.request("/create-market", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async listMarkets() {
    return this.request("/markets");
  }

  async getResults(marketId: string) {
    return this.request(`/results/${marketId}`);
  }

  // ── Debate ───────────────────────────────────────
  async runDebate(marketId: string, context?: string) {
    return this.request("/run-debate", {
      method: "POST",
      body: JSON.stringify({
        market_id: marketId,
        additional_context: context,
      }),
    });
  }

  async getReasoningTree(marketId: string) {
    return this.request(`/reasoning-tree/${marketId}`);
  }

  // ── Validators ───────────────────────────────────
  async getValidators() {
    return this.request("/validators");
  }

  // ── External API ─────────────────────────────────
  async predictWithReasoning(question: string, category: string = "general") {
    return this.request("/predict-with-reasoning", {
      method: "POST",
      body: JSON.stringify({ question, category }),
    });
  }

  // ── Health ───────────────────────────────────────
  async health() {
    return this.request("/health");
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
