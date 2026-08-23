import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createApplication } from '../api/applications'
import { makeApplication } from '../test/factories'
import { ApplicationForm } from './ApplicationForm'

vi.mock('../api/applications', () => ({
  createApplication: vi.fn(),
}))

describe('ApplicationForm', () => {
  beforeEach(() => {
    vi.mocked(createApplication).mockReset()
  })

  it('creates an application and refreshes the dashboard', async () => {
    const user = userEvent.setup()
    const onCreated = vi.fn()

    vi.mocked(createApplication).mockResolvedValue(
      makeApplication(),
    )

    render(<ApplicationForm onCreated={onCreated} />)

    await user.type(
      screen.getByLabelText('Şirket adı'),
      '  OpenAI  ',
    )
    await user.type(
      screen.getByLabelText('Pozisyon'),
      '  Backend Engineer  ',
    )
    await user.selectOptions(
      screen.getByLabelText('Başlangıç durumu'),
      'applied',
    )
    await user.click(
      screen.getByRole('button', {
        name: 'Başvuruyu kaydet',
      }),
    )

    expect(createApplication).toHaveBeenCalledWith({
      company_name: 'OpenAI',
      job_title: 'Backend Engineer',
      status: 'applied',
      follow_up_at: null,
      source: null,
      job_url: null,
      notes: '',
    })
    expect(onCreated).toHaveBeenCalledOnce()
    expect(
      await screen.findByText(
        'Başvuru başarıyla kaydedildi.',
      ),
    ).toBeInTheDocument()
  })
})
