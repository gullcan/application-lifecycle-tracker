import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  archiveApplication,
  updateApplication,
} from '../api/applications'
import { makeApplication } from '../test/factories'
import { ApplicationDetailsControl } from './ApplicationDetailsControl'

vi.mock('../api/applications', () => ({
  archiveApplication: vi.fn(),
  restoreApplication: vi.fn(),
  updateApplication: vi.fn(),
}))

describe('ApplicationDetailsControl', () => {
  beforeEach(() => {
    vi.mocked(updateApplication).mockReset()
    vi.mocked(archiveApplication).mockReset()
  })

  it('updates details and refreshes the list', async () => {
    const user = userEvent.setup()
    const onUpdated = vi.fn()
    const application = makeApplication({
      source: 'linkedin',
      notes: 'Initial note',
    })
    vi.mocked(updateApplication).mockResolvedValue(
      application,
    )

    render(
      <ApplicationDetailsControl
        application={application}
        onUpdated={onUpdated}
      />,
    )

    await user.click(
      screen.getByText('Detaylar ve düzenleme'),
    )
    await user.click(
      screen.getByRole('button', { name: 'Düzenle' }),
    )
    const notes = screen.getByLabelText('Notlar')
    await user.clear(notes)
    await user.type(notes, 'Updated note')
    await user.click(
      screen.getByRole('button', {
        name: 'Değişiklikleri kaydet',
      }),
    )

    expect(updateApplication).toHaveBeenCalledWith(
      application.id,
      expect.objectContaining({ notes: 'Updated note' }),
    )
    expect(onUpdated).toHaveBeenCalledOnce()
  })
})
