import { expect, test } from "@playwright/test";

const accountFixture = {
  accounts: [
    {
      id: 7,
      email: "user@example.com",
      google_sub: "sub-7",
      scopes: "openid email profile",
    },
  ],
};

const messageFixture = [
  {
    id: "msg-1",
    subject: "Subject One",
    from: "sender@example.com",
    snippet: "This is a snippet.",
    date: "2024-01-01T00:00:00Z",
  },
];

test("accounts page renders one mocked account", async ({ page }) => {
  await page.route("**/api/accounts", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(accountFixture),
    });
  });

  await page.goto("/accounts");

  await expect(page.getByRole("heading", { name: "Connected Gmail Accounts" })).toBeVisible();
  await expect(page.getByText("user@example.com")).toBeVisible();
  await expect(page.getByRole("link", { name: "View messages" })).toBeVisible();
});

test("clicking View messages navigates to details page and renders mocked messages", async ({ page }) => {
  await page.route("**/api/accounts", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(accountFixture),
    });
  });
  await page.route("**/api/accounts/7/messages", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(messageFixture),
    });
  });

  await page.goto("/accounts");
  await page.getByRole("link", { name: "View messages" }).click();

  await expect(page).toHaveURL(/\/accounts\/7$/);
  await expect(page.getByRole("heading", { name: "Account Messages" })).toBeVisible();
  await expect(page.getByText("Subject One")).toBeVisible();
  await expect(page.getByText("sender@example.com")).toBeVisible();
  await expect(page.getByText("This is a snippet.")).toBeVisible();
});

test("messages page shows graceful error states for 404 and 400", async ({ page }) => {
  await page.route("**/api/accounts/404/messages", async (route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Account not found" }),
    });
  });

  await page.goto("/accounts/404");
  await expect(page.getByText("Error: Account not found.")).toBeVisible();

  await page.route("**/api/accounts/400/messages", async (route) => {
    await route.fulfill({
      status: 400,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Account token invalid" }),
    });
  });

  await page.goto("/accounts/400");
  await expect(page.getByText("Error: Unable to list messages for this account.")).toBeVisible();
});

test("messages page shows loading state while request is delayed", async ({ page }) => {
  await page.route("**/api/accounts/9/messages", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(messageFixture),
    });
  });

  await page.goto("/accounts/9");
  await expect(page.getByText("Loading messages...")).toBeVisible();
  await expect(page.getByText("Subject One")).toBeVisible();
});
