import { expect, type APIRequestContext, type Page } from "@playwright/test";

const API = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";
export const E2E_EMAIL = process.env.E2E_EMAIL ?? "demo@finflowia.com";
export const E2E_PASSWORD = process.env.E2E_PASSWORD ?? "demo1234";

// Everything the tests create starts with a prefix so cleanup can find it
// without touching the account's real data. It includes the browser project
// name because projects run in parallel on the same account and must not
// clean up each other's rows.
export const E2E_PREFIX = "e2e-";
export const prefixFor = (projectName: string) => `${E2E_PREFIX}${projectName.replace(/\W/g, "")}-`;

export async function apiLogin(request: APIRequestContext): Promise<string> {
  const res = await request.post(`${API}/auth/login`, {
    data: { email: E2E_EMAIL, password: E2E_PASSWORD },
  });
  expect(res.ok(), "demo user must exist (run scripts/seed_db.py)").toBeTruthy();
  return (await res.json()).data.access_token as string;
}

/** Start the page already authenticated, skipping the login form. */
export async function loginViaApi(page: Page, request: APIRequestContext): Promise<string> {
  // global-setup logs in once; fall back to a fresh login if run without it.
  const token = process.env.E2E_TOKEN ?? (await apiLogin(request));
  await page.addInitScript((t) => {
    localStorage.setItem("finflowia-auth", JSON.stringify({ state: { token: t, user: null }, version: 0 }));
  }, token);
  return token;
}

export async function createTransactionViaApi(
  request: APIRequestContext,
  token: string,
  data: { description: string; amount: string; transaction_type: "income" | "expense" },
): Promise<void> {
  const res = await request.post(`${API}/transactions`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { ...data, transaction_date: new Date().toISOString().slice(0, 10), category: "other" },
  });
  expect(res.ok()).toBeTruthy();
}

export async function cleanupE2eTransactions(
  request: APIRequestContext,
  token: string,
  prefix: string,
): Promise<void> {
  const headers = { Authorization: `Bearer ${token}` };
  const list = await request.get(`${API}/transactions?page_size=100`, { headers });
  if (!list.ok()) return;
  const rows = (await list.json()).data as { id: string; description: string }[];
  for (const row of rows.filter((r) => r.description.startsWith(prefix))) {
    await request.delete(`${API}/transactions/${row.id}`, { headers });
  }
}

export const uniqueName = (prefix: string, label: string) => `${prefix}${label}-${Date.now()}`;

/** Navigate with the sidebar link, opening the hamburger menu first on narrow screens. */
export async function gotoViaSidebar(page: Page, href: string): Promise<void> {
  const menu = page.locator('[data-testid="open-menu"]');
  if (await menu.isVisible()) await menu.click();
  await page.click(`a[href="${href}"]`);
}
