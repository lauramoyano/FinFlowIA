import { test, expect } from "@playwright/test";
import { E2E_EMAIL, E2E_PASSWORD } from "./helpers";

test.describe("Authentication", () => {
  // The backend allows 10 /auth requests per minute per IP (brute-force
  // protection) and every UI login also calls /auth/me. The login form has no
  // viewport-specific logic, so exercise it on desktop only; also avoid
  // re-running the suite several times within one minute.
  test.skip(({ isMobile }) => isMobile, "login form is covered on desktop");

  test("unauthenticated users are redirected to login from every app route", async ({ page }) => {
    for (const path of ["/home", "/dashboard", "/transactions", "/products", "/reports"]) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login$/);
    }
  });

  test("login form shows error with wrong credentials", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[name="email"]', "wrong@example.com");
    await page.fill('[name="password"]', "wrongpassword");
    await page.click('[type="submit"]');

    await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("valid credentials land on /home", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[name="email"]', E2E_EMAIL);
    await page.fill('[name="password"]', E2E_PASSWORD);
    await page.click('[type="submit"]');

    await expect(page).toHaveURL(/\/home$/);
    await expect(page.locator('[data-testid="page-title"]')).toBeVisible();
  });
});
