import { test, expect } from '@playwright/test';

test('page finder supports keyboard search, empty results, navigation and escape', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Control+k');
  const dialog = page.getByRole('dialog', { name: 'Find a page' });
  await expect(dialog).toBeVisible();
  const search = page.getByRole('textbox', { name: 'Search pages' });
  await expect(search).toBeFocused();
  await search.fill('no matching destination');
  await expect(dialog.getByText('No matching pages. Try users, access, or audit.')).toBeVisible();
  await search.fill('audit');
  await search.press('Enter');
  await expect(page).toHaveURL(/\/audit$/);
  await expect(dialog).toHaveCount(0);
  await expect(page.locator('.breadcrumbs')).toContainText('Audit explorer');
  await expect(page).toHaveTitle('Audit explorer · AccessLedger');
  await page.getByRole('button', { name: 'Find a page', exact: true }).click();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Find a page', exact: true })).toBeFocused();
});

test('all pages fit a mobile viewport and dialogs remain operable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of ['/', '/users', '/roles', '/resources', '/access', '/audit']) {
    await page.goto(path);
    await page.waitForLoadState('networkidle');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), path).toBe(true);
  }
  await page.goto('/users');
  await page.getByRole('button', { name: 'Add employee' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByLabel('Full name', { exact: true })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
});
