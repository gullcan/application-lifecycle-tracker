import { expect, test } from '@playwright/test'


test('manages a personal application from creation to archive', async ({
  page,
}) => {
  await page.goto('/')

  await expect(page.getByRole('status')).toContainText(
    'API: Bağlı',
  )

  const creationForm = page.locator('.application-form')
  await creationForm.getByLabel('Şirket adı').fill(
    'E2E Company',
  )
  await creationForm.getByLabel('Pozisyon').fill(
    'Python Engineer',
  )
  await creationForm.getByLabel('Başvuru kaynağı').selectOption(
    'linkedin',
  )
  await creationForm.getByLabel('İlan bağlantısı').fill(
    'https://example.com/jobs/e2e',
  )
  await creationForm.getByLabel('Notlar').fill(
    'E2E görüşme notu',
  )
  await creationForm.getByRole('button', {
    name: 'Başvuruyu kaydet',
  }).click()

  await expect(page.getByText('E2E Company')).toBeVisible()
  await page.getByText('Detaylar ve düzenleme').click()
  await expect(
    page.getByText('E2E görüşme notu'),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Düzenle' }).click()
  const editForm = page.locator('.details-edit-form')
  await editForm.getByLabel('Pozisyon').fill(
    'Senior Python Engineer',
  )
  await editForm.getByRole('button', {
    name: 'Değişiklikleri kaydet',
  }).click()

  await expect(
    page.getByText('Senior Python Engineer'),
  ).toBeVisible()

  await page.getByText('Detaylar ve düzenleme').click()
  await page.getByRole('button', { name: 'Arşivle' }).click()
  await expect(page.getByText('E2E Company')).toHaveCount(0)

  await page.getByLabel('Arşivlenenleri göster').check()
  await expect(page.getByText('E2E Company')).toBeVisible()
  await expect(page.getByText('Arşivlendi')).toBeVisible()

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('link', { name: 'CSV indir' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('applications.csv')
})
