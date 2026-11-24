import { test, expect, type Page } from "@playwright/test";
import { gotoViaSidebar, loginViaApi } from "./helpers";

// The orchestrator response is mocked so these tests are deterministic and
// don't spend LLM tokens; routing/extraction quality is measured separately
// by backend/scripts/evaluate_router.py.
function mockOrchestrator(page: Page, data: Record<string, unknown>) {
  return page.route("**/orchestrator/message", (route) =>
    route.fulfill({
      json: {
        data: {
          conversation_id: "e2e-conv",
          message: null,
          message_params: null,
          draft: null,
          estimate: null,
          sales_goal: null,
          financial_recommendation: null,
          period_summary: null,
          agent: null,
          error_code: null,
          ...data,
        },
        message: "Success",
      },
    }),
  );
}

test.describe("Home chat", () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaApi(page, request);
  });

  test("keeps the conversation and the typed draft when switching tabs", async ({ page }) => {
    await mockOrchestrator(page, {
      kind: "confirm_transaction",
      draft: {
        description: "nafta",
        amount: "2500",
        transaction_type: "expense",
        transaction_date: "2026-11-01",
        category: "transport",
        confidence: 0.9,
        error: null,
      },
    });
    await page.goto("/home");

    const input = page.locator('[data-testid="chat-text-input"]');
    await input.fill("gasté 2500 en nafta");
    await page.click('[data-testid="chat-send"]');
    await expect(page.locator('[data-testid="chat-confirm"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-messages"]')).toContainText("gasté 2500 en nafta");

    await input.fill("texto a medio escribir");

    await gotoViaSidebar(page, "/dashboard");
    await expect(page).toHaveURL(/\/dashboard$/);
    await gotoViaSidebar(page, "/home");

    await expect(page.locator('[data-testid="chat-messages"]')).toContainText("gasté 2500 en nafta");
    await expect(page.locator('[data-testid="chat-confirm"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-text-input"]')).toHaveValue("texto a medio escribir");
  });

  test("renders a sales goal split across several products", async ({ page }) => {
    await mockOrchestrator(page, {
      kind: "sales_goal_result",
      sales_goal: {
        goal_amount: "300000",
        items: [
          { product_name: "torta", quantity_needed: 600, unit_sale_price: "250", unit_insumos_cost: "150", insumos_investment: "90000", projected_revenue: "150000", estimated_profit: "60000" },
          { product_name: "alfajor", quantity_needed: 500, unit_sale_price: "300", unit_insumos_cost: "200", insumos_investment: "100000", projected_revenue: "150000", estimated_profit: "50000" },
        ],
        insumos_investment: "190000",
        projected_revenue: "300000",
        estimated_profit: "110000",
      },
    });
    await page.goto("/home");

    await page.locator('[data-testid="chat-text-input"]').fill("quiero vender 300000 en la feria");
    await page.click('[data-testid="chat-send"]');

    const result = page.locator('[data-testid="chat-sales-goal-result"]');
    await expect(result).toContainText("torta");
    await expect(result).toContainText("alfajor");
    await expect(result).toContainText("600");
    await expect(result).toContainText("500");
  });
});
