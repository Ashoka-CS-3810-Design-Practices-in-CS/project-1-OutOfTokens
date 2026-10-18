import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

// the real website and backend, used the way a rider would

const fromBox = (page: Page) => page.locator('[data-slot="autocomplete-trigger"]').nth(0)
const toBox = (page: Page) => page.locator('[data-slot="autocomplete-trigger"]').nth(1)
const findRoute = (page: Page) => page.getByRole('button', { name: 'Find route' })

// open a station box, type, and click the suggestion with exactly this name
async function choose(page: Page, box: 'from' | 'to', typed: string, name: string) {
  await (box === 'from' ? fromBox(page) : toBox(page)).click()
  await page.keyboard.type(typed)
  await page.getByRole('option', { name: new RegExp(`^${name}`) }).click()
}

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Loading stations…')).toBeHidden()
})

test('the map shows every station and the boxes can be used', async ({ page }) => {
  await expect(page.locator('.station-node')).toHaveCount(257)
  await expect(page.locator('.metro-edges line')).toHaveCount(272)
  await expect(fromBox(page)).toBeEnabled()
})

test('clicking a station box opens the search before anything is typed', async ({ page }) => {
  // the 15 Oct bug: an empty list refused to open, so the boxes did nothing
  await fromBox(page).click()
  await expect(page.getByPlaceholder('Type a station name')).toBeVisible()
  await expect(page.getByText('Start typing a station name')).toBeVisible()
})

test('Find route stays disabled until both stations are chosen', async ({ page }) => {
  await expect(findRoute(page)).toBeDisabled()
  await expect(page.getByText('Select both stations.')).toBeVisible()
  await choose(page, 'from', 'new del', 'New Delhi')
  await expect(findRoute(page)).toBeDisabled()
  await choose(page, 'to', 'ito', 'ITO')
  await expect(findRoute(page)).toBeEnabled()
})

test('New Delhi to ITO shows a different route on each tab', async ({ page }) => {
  await choose(page, 'from', 'new del', 'New Delhi')
  await choose(page, 'to', 'ito', 'ITO')
  await findRoute(page).click()

  const stats = page.locator('.route-stats')
  await expect(page.getByText('Fastest route')).toBeVisible()
  await expect(stats).toContainText('17 min')
  await expect(stats).toContainText('6.8 km')

  await page.getByRole('tab', { name: 'Minimum stations' }).click()
  await expect(stats).toContainText('18 min')
  await expect(stats).toContainText('3.6 km')

  await page.getByRole('tab', { name: 'Minimum interchanges' }).click()
  await expect(stats).toContainText('17 min')

  // the selected route is drawn on top of the map
  await expect(page.locator('line.route-edge:not(.route-edge-faded)').first()).toBeVisible()
})

test('a station name with no match says so', async ({ page }) => {
  await fromBox(page).click()
  await page.keyboard.type('zzzz')
  await expect(page.getByText('No matching station found.')).toBeVisible()
})

test('typing a name without picking it asks the rider to choose from the list', async ({ page }) => {
  await fromBox(page).click()
  await page.keyboard.type('rajiv')
  // close the list by clicking elsewhere; Escape would only clear the typed text
  await page.mouse.click(200, 700)
  await expect(page.getByText('Please choose a station from the list')).toBeVisible()
})

test('the same station cannot be chosen twice', async ({ page }) => {
  await choose(page, 'from', 'rajiv', 'Rajiv Chowk')
  await choose(page, 'to', 'rajiv', 'Rajiv Chowk')
  await expect(page.getByText('Source and destination must be different.')).toBeVisible()
  await expect(findRoute(page)).toBeDisabled()
})

test('Reset clears the stations and the route', async ({ page }) => {
  await choose(page, 'from', 'chandni', 'Chandni Chowk')
  await choose(page, 'to', 'rajiv', 'Rajiv Chowk')
  await findRoute(page).click()
  await expect(page.locator('.route-stats')).toContainText('6 min')

  await page.getByRole('button', { name: 'Reset' }).click()
  await expect(page.locator('.route-stats')).toHaveCount(0)
  await expect(fromBox(page)).toContainText('Choose start station')
  await expect(findRoute(page)).toBeDisabled()
})

test('clicking a station on the map shows its details', async ({ page }) => {
  await page.getByRole('button', { name: 'Kashmere Gate', exact: true }).click()
  const popup = page.getByRole('dialog')
  await expect(popup).toContainText('Kashmere Gate')
  await expect(popup).toContainText('Interchange station')
  await expect(popup.getByRole('listitem')).toHaveCount(3)
  await page.keyboard.press('Escape')
  await expect(popup).toHaveCount(0)
})

test('if the map data cannot be loaded, the page says so and offers Reload', async ({ page }) => {
  await page.route('**/api/network', (route) => route.abort())
  await page.goto('/')
  await expect(page.getByText('Map data could not be loaded.')).toBeVisible()
  await page.unroute('**/api/network')
  await page.getByRole('button', { name: 'Reload' }).click()
  await expect(page.getByText('Map data could not be loaded.')).toBeHidden()
  await expect(fromBox(page)).toBeEnabled()
})

test('if a route request fails, the page says so and offers Retry', async ({ page }) => {
  await choose(page, 'from', 'new del', 'New Delhi')
  await choose(page, 'to', 'ito', 'ITO')
  await page.route('**/api/route', (route) => route.abort())
  await findRoute(page).click()
  await expect(page.getByText('Could not compute the route. Please try again.')).toBeVisible()
  await page.unroute('**/api/route')
  await page.getByRole('button', { name: 'Retry' }).click()
  await expect(page.locator('.route-stats')).toContainText('17 min')
})
