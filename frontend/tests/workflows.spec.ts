import { test, expect } from '@playwright/test';

test('employee registration, assignment, grant, evaluation and revocation retain history', async ({ page }) => {
  const token = `Browser ${Date.now()}`;
  await page.goto('/users');
  await page.getByRole('button', { name: 'Add employee' }).click();
  await page.getByLabel('Full name', { exact: true }).fill(token);
  await page.getByLabel('Email', { exact: true }).fill(`browser-${Date.now()}@example.com`);
  await page.getByLabel('Department', { exact: true }).selectOption({ label: 'Computer Science' });
  await page.getByRole('button', { name: 'Save employee' }).click();
  await expect(page.getByText('Employee created.', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Roles & permissions' }).click();
  await page.getByLabel('New role name').fill(token);
  await page.getByRole('button', { name: 'Create role', exact: true }).click();
  await expect(page.getByText('Role created.', { exact: true })).toBeVisible();
  await page.getByLabel('Employee', { exact: true }).selectOption({ label: token });
  await page.getByLabel('Role to assign').selectOption({ label: token });
  await page.getByRole('button', { name: 'Assign role', exact: true }).click();
  await expect(page.getByText('Role assigned.', { exact: true })).toBeVisible();
  await page.getByLabel('Role to configure').selectOption({ label: token });
  await page.getByLabel('Permission to grant').selectOption({ label: 'Reporting Database · READ' });
  await page.getByRole('button', { name: 'Grant permission', exact: true }).click();
  await expect(page.getByText('Permission granted.', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Access evaluation' }).click();
  await page.getByLabel('Employee', { exact: true }).selectOption({ label: token });
  await page.getByLabel('Resource', { exact: true }).selectOption({ label: 'Reporting Database' });
  await page.getByLabel('Action', { exact: true }).selectOption({ label: 'READ' });
  await page.getByRole('button', { name: 'Evaluate access', exact: true }).click();
  await expect(page.getByTestId('decision')).toHaveText('ALLOW');
  await page.getByRole('link', { name: 'Roles & permissions' }).click();
  await page.getByLabel('Employee', { exact: true }).selectOption({ label: token });
  await page.getByRole('button', { name: `Revoke ${token}`, exact: true }).click();
  await expect(page.getByText('Role revoked.', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Access evaluation' }).click();
  await page.getByLabel('Employee', { exact: true }).selectOption({ label: token });
  await page.getByLabel('Resource', { exact: true }).selectOption({ label: 'Reporting Database' });
  await page.getByLabel('Action', { exact: true }).selectOption({ label: 'READ' });
  await page.getByRole('button', { name: 'Evaluate access', exact: true }).click();
  await expect(page.getByTestId('decision')).toHaveText('DENY');
  await page.getByRole('link', { name: 'Audit explorer' }).click();
  await page.getByLabel('Search audit').fill(token);
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.getByRole('cell', { name: 'ALLOW', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'DENY', exact: true })).toBeVisible();
});

test('all six pages render with no browser errors and mobile navigation works', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  for (const path of ['/', '/users', '/roles', '/resources', '/access', '/audit']) {
    await page.goto(path);
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(0);
  }
  expect(errors).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('link', { name: 'Audit explorer' }).click();
  await expect(page.locator('h1')).toHaveText('Audit explorer');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('pending evaluation keeps the submitted employee, resource and action fixed', async ({ page }) => {
  await page.goto('/access');
  await page.getByLabel('Employee', { exact: true }).selectOption({ label: 'Priya Sharma' });
  await page.getByLabel('Resource', { exact: true }).selectOption({ label: 'Reporting Database' });
  await page.getByLabel('Action', { exact: true }).selectOption({ label: 'READ' });
  await page.route('**/api/v1/evaluations', async route => {
    const response = await route.fetch();
    await new Promise(resolve => setTimeout(resolve, 1200));
    await route.fulfill({ response });
  });
  await page.getByRole('button', { name: 'Evaluate access', exact: true }).click();
  await expect(page.getByLabel('Employee', { exact: true })).toBeDisabled();
  await expect(page.getByLabel('Resource', { exact: true })).toBeDisabled();
  await expect(page.getByLabel('Action', { exact: true })).toBeDisabled();
  await expect(page.getByTestId('decision')).toHaveText('ALLOW');
  await expect(page.getByLabel('Employee', { exact: true })).toBeEnabled();
});
