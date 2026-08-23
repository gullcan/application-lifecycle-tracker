import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { ApplicationStatusHistory } from './ApplicationStatusHistory'

describe('ApplicationStatusHistory', () => {
  it('shows an empty state when no status changed', () => {
    render(<ApplicationStatusHistory history={[]} />)

    expect(
      screen.getByText('Değişiklik yok'),
    ).toBeInTheDocument()
  })

  it('shows immutable transitions in an expandable history', async () => {
    const user = userEvent.setup()

    render(
      <ApplicationStatusHistory
        history={[
          {
            previous_status: 'applied',
            new_status: 'screening',
            changed_at: '2026-08-24T09:30:00Z',
          },
        ]}
      />,
    )

    await user.click(
      screen.getByText('1 durum değişikliği'),
    )

    expect(
      screen.getByText('Başvuruldu → Ön görüşme'),
    ).toBeVisible()
  })
})
