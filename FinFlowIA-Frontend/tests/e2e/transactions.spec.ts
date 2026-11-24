import { test, expect } from "@playwright/test";
import {
  cleanupE2eTransactions,
  createTransactionViaApi,
  gotoViaSidebar,
  loginViaApi,
  prefixFor,
  uniqueName,
} from "./helpers";

test.describe("Transaction Management", () => {
  // Same account for every test: run in order so cleanup never removes
  // rows another test is still using.
  test.describe.configure({ mode: "serial" });

  let token: string;
  let prefix: string;

  test.beforeEach(async ({ page, request }, testInfo) => {
    token = await loginViaApi(page, request);
    prefix = prefixFor(testInfo.project.name);
  });

  test.afterEach(async ({ request }) => {
    await cleanupE2eTransactions(request, token, prefix);
  });

  async function openManualForm(page: import("@playwright/test").Page) {
    await page.goto("/transactions");
    await page.click('[data-testid="add-transaction"]');
    // The chat is the default entry point; the manual form sits behind a link.
    await page.click('[data-testid="switch-to-form"]');
  }

  test("user can register a transaction and see it in the list", async ({ page }) => {
    const description = uniqueName(prefix, "compra");
    await openManualForm(page);

    await page.fill('input[name="description"]', description);
    await page.fill('input[name="amount"]', "150.00");
    await page.selectOption('select[name="type"]', "expense");
    await page.click('[type="submit"]');

    await expect(page.locator('[data-testid="transaction-list"]').first()).toContainText(description);
  });

  test("user can filter transactions by type", async ({ page, request }) => {
    await createTransactionViaApi(request, token, {
      description: uniqueName(prefix, "ingreso"),
      amount: "5000.00",
      transaction_type: "income",
    });
    await page.goto("/transactions");

    await page.selectOption("form select >> nth=0", "income");
    await page.click('[data-testid="apply-filters-button"]');

    // Selector is on a data attribute (not translated text) so it works in es/en.
    // :visible because the table (desktop) and the cards (mobile) both render.
    await expect(page.locator('[data-transaction-type="income"]:visible').first()).toBeVisible();
    await expect(page.locator('[data-transaction-type="expense"]')).toHaveCount(0);
  });

  test("user can delete a transaction", async ({ page, request }) => {
    const description = uniqueName(prefix, "borrar");
    await createTransactionViaApi(request, token, { description, amount: "100.00", transaction_type: "expense" });
    await page.goto("/transactions");

    const list = page.locator('[data-testid="transaction-list"]').first();
    await expect(list).toContainText(description);

    // Delete only the row we created, not the first one in the account. The
    // row is a table <tr> on desktop and a card on mobile; only one is visible.
    await page
      .locator('tr, [data-testid="transaction-row-mobile"]')
      .filter({ hasText: description })
      .locator('[data-testid="delete-transaction-button"]:visible')
      .click();

    await expect(list).not.toContainText(description);
  });

  test("dashboard loads after creating a transaction", async ({ page }) => {
    await openManualForm(page);
    await page.fill('input[name="description"]', uniqueName(prefix, "venta"));
    await page.fill('input[name="amount"]', "5000.00");
    await page.selectOption('select[name="type"]', "income");
    // Wait for the save to finish so cleanup sees the row instead of racing it.
    await Promise.all([
      page.waitForResponse((r) => r.url().includes("/transactions") && r.request().method() === "POST"),
      page.click('[type="submit"]'),
    ]);

    await gotoViaSidebar(page, "/dashboard");
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.locator('[data-testid="page-title"]')).toBeVisible();
  });
});
