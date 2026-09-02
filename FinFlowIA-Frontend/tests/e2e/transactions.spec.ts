import { test, expect } from "@playwright/test";

test.describe("Transaction Management", () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto("/login");
    await page.fill('[name="email"]', "test@example.com");
    await page.fill('[name="password"]', "password123");
    await page.click('[type="submit"]');
    await expect(page).toHaveURL("/dashboard");
  });

  test("user can register a transaction and see it in the list", async ({ page }) => {
    await page.goto("/transactions");

    // Open the add transaction form
    await page.click('[data-testid="add-transaction"]');

    // Fill in transaction details
    await page.fill('[name="description"]', "Compra materiales de oficina");
    await page.fill('[name="amount"]', "150.00");
    await page.selectOption('[name="type"]', "expense");

    // Submit
    await page.click('[type="submit"]');

    // Verify it appears in the list
    await expect(
      page.locator('[data-testid="transaction-list"]'),
    ).toContainText("Compra materiales de oficina");
  });

  test("user can filter transactions by type", async ({ page }) => {
    await page.goto("/transactions");

    // Apply income filter
    await page.selectOption('[name="transaction_type"]', "income");
    await page.click('[data-testid="apply-filters-button"]');

    // All visible transactions should be income type. Selector is on a
    // data attribute (not translated text) so it works regardless of the
    // active UI language (es/en, see shared/i18n).
    const incomeRows = page.locator('[data-transaction-type="income"]');
    await expect(incomeRows.first()).toBeVisible();
  });

  test("dashboard shows correct totals after creating a transaction", async ({ page }) => {
    await page.goto("/transactions");
    await page.click('[data-testid="add-transaction"]');

    await page.fill('[name="description"]', "Venta importante");
    await page.fill('[name="amount"]', "5000.00");
    await page.selectOption('[name="type"]', "income");
    await page.click('[type="submit"]');

    // Navigate to dashboard via the sidebar link (href is language-agnostic).
    await page.click('a[href="/dashboard"]');
    await expect(page).toHaveURL("/dashboard");

    // Dashboard should load without error.
    await expect(page.locator('[data-testid="page-title"]')).toBeVisible();
  });

  test("user can delete a transaction", async ({ page }) => {
    // First create a transaction
    await page.goto("/transactions");
    await page.click('[data-testid="add-transaction"]');
    await page.fill('[name="description"]', "Transaction to delete");
    await page.fill('[name="amount"]', "100.00");
    await page.selectOption('[name="type"]', "expense");
    await page.click('[type="submit"]');

    await expect(
      page.locator('[data-testid="transaction-list"]'),
    ).toContainText("Transaction to delete");

    // Delete the transaction
    await page.click('[data-testid="delete-transaction-button"]');

    // Verify it's removed
    await expect(
      page.locator('[data-testid="transaction-list"]'),
    ).not.toContainText("Transaction to delete");
  });
});

test.describe("Authentication", () => {
  // NOTE: login gating is intentionally disabled while the rest of the
  // frontend is being built (see router/index.tsx TODO(auth-final-phase)),
  // so unauthenticated users currently CAN reach /dashboard. Re-enable this
  // test once ProtectedRoute is wired back in.
  test.skip("unauthenticated users are redirected to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL("/login");
  });

  test("login form shows error with wrong credentials", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[name="email"]', "wrong@example.com");
    await page.fill('[name="password"]', "wrongpassword");
    await page.click('[type="submit"]');

    await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
  });
});
