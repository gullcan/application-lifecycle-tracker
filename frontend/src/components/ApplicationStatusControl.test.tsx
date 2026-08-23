import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { changeApplicationStatus } from '../api/applications'
import { makeApplication } from '../test/factories'
import { ApplicationStatusControl } from './ApplicationStatusControl'

vi.mock('../api/applications', () => ({
  changeApplicationStatus: vi.fn(),
}))

describe('ApplicationStatusControl', () => {
  beforeEach(() => {
    vi.mocked(changeApplicationStatus).mockReset()
  })

  it('shows the backend domain error for an invalid transition', async () => {
    const user = userEvent.setup()
    const onUpdated = vi.fn()

    vi.mocked(changeApplicationStatus).mockRejectedValue(
      new Error(
        "cannot change status from 'screening' to 'applied'",
      ),
    )

    render(
      <ApplicationStatusControl
        application={
          makeApplication({ status: 'screening' })
        }
        onUpdated={onUpdated}
      />,
    )

    await user.selectOptions(
      screen.getByLabelText(
        'OpenAI başvuru durumu',
      ),
      'applied',
    )
    await user.click(
      screen.getByRole('button', {
        name: 'Güncelle',
      }),
    )

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(
      "cannot change status from 'screening' to 'applied'",
    )
    expect(onUpdated).not.toHaveBeenCalled()
  })
})
