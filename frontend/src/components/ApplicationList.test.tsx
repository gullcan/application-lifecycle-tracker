import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listApplications } from '../api/applications'
import { makeApplication } from '../test/factories'
import { ApplicationList } from './ApplicationList'

vi.mock('../api/applications', () => ({
  listApplications: vi.fn(),
  changeApplicationStatus: vi.fn(),
  scheduleApplicationFollowUp: vi.fn(),
  clearApplicationFollowUp: vi.fn(),
  updateApplication: vi.fn(),
  archiveApplication: vi.fn(),
  restoreApplication: vi.fn(),
  applicationExportUrl: () => (
    '/api/applications/export.csv'
  ),
}))

describe('ApplicationList', () => {
  beforeEach(() => {
    vi.mocked(listApplications).mockReset()
    vi.mocked(listApplications).mockResolvedValue([
      makeApplication(),
    ])
  })

  it('loads applications and sends the selected status filter', async () => {
    const user = userEvent.setup()

    render(
      <ApplicationList
        refreshVersion={0}
        onUpdated={vi.fn()}
      />,
    )

    expect(
      await screen.findByText('OpenAI'),
    ).toBeInTheDocument()

    await user.selectOptions(
      screen.getByLabelText('Duruma göre filtrele'),
      'interview',
    )

    await waitFor(() => {
      expect(listApplications).toHaveBeenLastCalledWith(
        expect.objectContaining({
          status: 'interview',
          limit: 11,
          offset: 0,
        }),
      )
    })
  })
})
