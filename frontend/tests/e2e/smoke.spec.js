import { expect, test } from "@playwright/test";

test("home loads and pricing is reachable", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  await page.goto("/pricing");
  await expect(page.getByText("Tarifs")).toBeVisible();
});

test("auth pages render", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /Connexion/i })).toBeVisible();

  await page.goto("/register");
  await expect(page.getByRole("heading", { name: /Cree ton compte/i })).toBeVisible();
});
