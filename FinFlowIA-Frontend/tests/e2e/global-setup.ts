import { request } from "@playwright/test";
import { apiLogin } from "./helpers";

// The backend limits /auth to 10 requests/minute per IP (brute-force
// protection), so log in once for the whole run instead of once per test.
// Env vars set here are inherited by the test workers.
export default async function globalSetup() {
  const api = await request.newContext();
  process.env.E2E_TOKEN = await apiLogin(api);
  await api.dispose();
}
