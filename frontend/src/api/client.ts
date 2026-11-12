const TOKEN_KEY = "analytics_token";
export function getToken(){ return localStorage.getItem(TOKEN_KEY); }
export function setToken(token:string){ localStorage.setItem(TOKEN_KEY, token); }
export function clearToken(){ localStorage.removeItem(TOKEN_KEY); }

export interface ApiErrorBody {
  detail?: string;
  conflict?: boolean;
  current_version?: number;
  latest_decision?: {
    id: string;
    decision: string;
    reason: string;
    version: number;
    reviewer_id: string;
    reviewer_name: string;
    created_at: string;
  } | null;
}

export class ApiError extends Error {
  status: number;
  body: ApiErrorBody;
  constructor(status:number, body:ApiErrorBody){
    super(typeof body.detail === "string" ? body.detail : "请求失败");
    this.status = status;
    this.body = body;
  }
}

export async function api<T>(path:string, init:RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`/api${path}`, {...init, headers});
  if (!response.ok) {
    const payload = await response.json().catch(() => ({detail:"请求失败"}));
    throw new ApiError(response.status, payload);
  }
  return response.json();
}
