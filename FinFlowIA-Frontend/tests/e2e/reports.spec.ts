import { test, expect } from "@playwright/test";
import { loginViaApi } from "./helpers";
import { readFileSync } from "node:fs";

test.describe("Report download", () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaApi(page, request);
    await page.goto("/reports");
    await page.locator('input[type="date"]').nth(0).fill("2026-01-01");
    await page.locator('input[type="date"]').nth(1).fill("2026-12-31");
  });

  test("downloads a CSV with the selected period", async ({ page }) => {
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: /csv/i }).click(),
    ]);

    expect(download.suggestedFilename()).toBe("report_2026-01-01_2026-12-31.csv");
    const content = readFileSync(await download.path(), "utf-8");
    expect(content).toContain("2026-01-01");
  });

  test("downloads a real PDF, not placeholder text", async ({ page }) => {
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: /pdf/i }).click(),
    ]);

    expect(download.suggestedFilename()).toBe("report_2026-01-01_2026-12-31.pdf");
    const bytes = readFileSync(await download.path());
    expect(bytes.subarray(0, 5).toString()).toBe("%PDF-");
  });
});
