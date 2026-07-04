import { test, expect, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill("admin@local");
  await page.locator('input[type="password"]').fill("admin1234");
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

test("connexion et affichage du dashboard", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  // KPI cards présentes
  await expect(page.getByText("Hosts Online")).toBeVisible();
  await expect(page.getByText("Services OK")).toBeVisible();
});

test("identifiants invalides -> message d'erreur", async ({ page }) => {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill("admin@local");
  await page.locator('input[type="password"]').fill("mauvais");
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page.getByText("Identifiants invalides")).toBeVisible();
});

test("navigation entre les pages principales", async ({ page }) => {
  await login(page);
  for (const [link, heading] of [
    ["Hosts", "Hosts"],
    ["Checks", "Checks"],
    ["Incidents", "Incident Center"],
    ["Reports", "Reports"],
    ["Settings", "Settings"],
  ] as const) {
    await page.getByRole("link", { name: link }).click();
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
  }
});

test("redirection vers login si non authentifié", async ({ page }) => {
  await page.goto("/hosts");
  await expect(page).toHaveURL(/\/login/);
});
