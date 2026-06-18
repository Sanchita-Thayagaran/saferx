import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axios from 'axios'
import App from '../App'

vi.mock('axios')

function makeResponse({
  risk_level = 'GREEN',
  verified = true,
  emergency = false,
  report = null,
} = {}) {
  return {
    data: {
      request_id: 'req-test-1',
      session_id: null,
      extracted_info: {
        drug_name: 'Paracetamol',
        active_ingredient: null,
        manufacturer: 'GlaxoSmithKline',
        batch_number: 'PAR-2024-001',
        expiry_date: null,
        dosage_form: null,
        strength: '500mg',
        country_of_origin: null,
        raw_input: 'Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001',
      },
      database_matches: [
        { source: 'WHO_GFMD', matched: true, alert_type: null, confidence: 0.97 },
        { source: 'FDA', matched: true, alert_type: null, confidence: 0.95 },
      ],
      risk_assessment: {
        level: risk_level,
        score: risk_level === 'RED' ? 0.95 : risk_level === 'YELLOW' ? 0.5 : 0.1,
        reasoning: 'Mock reasoning text.',
        flags: [],
        citations: [],
      },
      action_guidance: {
        summary: 'Mock summary.',
        steps: ['Step one.', 'Step two.'],
        contact_authority: emergency ? 'WHO GFMD' : null,
        emergency,
      },
      report,
      risk_level,
      verified,
      processing_time_ms: 12.3,
      timestamp: new Date().toISOString(),
      reasoning_trace: ['Step 1 — done.'],
      disclaimer: 'This is a decision-support tool only.',
    },
  }
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the header and tagline', () => {
    render(<App />)
    expect(screen.getByText('Safe')).toBeInTheDocument()
    expect(screen.getAllByText('Rx').length).toBeGreaterThan(0)
    expect(screen.getByText(/Know before you swallow\./i)).toBeInTheDocument()
  })

  it('disables the Verify button when input is empty', () => {
    render(<App />)
    const button = screen.getByRole('button', { name: /verify medicine/i })
    expect(button).toBeDisabled()
  })

  it('enables the Verify button once text is entered', async () => {
    const user = userEvent.setup()
    render(<App />)
    const textarea = screen.getByPlaceholderText(/describe the medicine/i)
    await user.type(textarea, 'Paracetamol 500mg')
    const button = screen.getByRole('button', { name: /verify medicine/i })
    expect(button).toBeEnabled()
  })

  it('submits typed input to POST /verify and renders a GREEN result', async () => {
    axios.post.mockResolvedValueOnce(makeResponse({ risk_level: 'GREEN', verified: true }))
    const user = userEvent.setup()
    render(<App />)

    const textarea = screen.getByPlaceholderText(/describe the medicine/i)
    await user.type(textarea, 'Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001')
    await user.click(screen.getByRole('button', { name: /verify medicine/i }))

    await waitFor(() => {
      expect(screen.getByText('VERIFIED SAFE')).toBeInTheDocument()
    })

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8000/verify',
      { input_text: 'Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001', locale: 'en' }
    )
  })

  it('clicking a demo button calls POST /verify/demo with the right scenario', async () => {
    axios.post.mockResolvedValueOnce(makeResponse({ risk_level: 'RED', verified: false, emergency: true }))
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /RED/i }))

    await waitFor(() => {
      expect(screen.getByText('COUNTERFEIT DETECTED')).toBeInTheDocument()
    })

    expect(axios.post).toHaveBeenCalledWith('http://localhost:8000/verify/demo?scenario=red')
  })

  it('shows the emergency banner for a RED result', async () => {
    axios.post.mockResolvedValueOnce(makeResponse({ risk_level: 'RED', verified: false, emergency: true }))
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /RED/i }))

    await waitFor(() => {
      expect(screen.getByText(/EMERGENCY — Immediate action required/i)).toBeInTheDocument()
    })
  })

  it('renders the regulatory report download button when a report is present', async () => {
    axios.post.mockResolvedValueOnce(
      makeResponse({
        risk_level: 'YELLOW',
        verified: false,
        report: { report_id: 'SAFERX-ABC123', generated_at: new Date().toISOString(), markdown: '# Report', json_payload: {} },
      })
    )
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /YELLOW/i }))

    await waitFor(() => {
      expect(screen.getByText('SAFERX-ABC123')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
  })

  it('does not render a report section when report is null (GREEN scenario)', async () => {
    axios.post.mockResolvedValueOnce(makeResponse({ risk_level: 'GREEN', verified: true, report: null }))
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /GREEN/i }))

    await waitFor(() => {
      expect(screen.getByText('VERIFIED SAFE')).toBeInTheDocument()
    })
    expect(screen.queryByRole('button', { name: /download/i })).not.toBeInTheDocument()
  })

  it('shows an error banner when the API call fails', async () => {
    axios.post.mockRejectedValueOnce(new Error('Network Error'))
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /GREEN/i }))

    await waitFor(() => {
      expect(screen.getByText(/Unable to reach SafeRx API\./i)).toBeInTheDocument()
    })
    expect(screen.getByText(/Network Error/i)).toBeInTheDocument()
  })

  it('dismisses the error banner when Dismiss is clicked', async () => {
    axios.post.mockRejectedValueOnce(new Error('Network Error'))
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /GREEN/i }))
    await waitFor(() => {
      expect(screen.getByText(/Unable to reach SafeRx API\./i)).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /dismiss/i }))

    await waitFor(() => {
      expect(screen.queryByText(/Unable to reach SafeRx API\./i)).not.toBeInTheDocument()
    })
  })

  it('toggles the Sources Checked panel open and closed', async () => {
    axios.post.mockResolvedValueOnce(makeResponse({ risk_level: 'GREEN', verified: true }))
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /GREEN/i }))
    await waitFor(() => {
      expect(screen.getByText(/Sources Checked/i)).toBeInTheDocument()
    })

    expect(screen.getAllByText('WHO GFMD')).toHaveLength(1) // header badge only, panel collapsed
    await user.click(screen.getByRole('button', { name: /Sources Checked/i }))
    await waitFor(() => {
      expect(screen.getAllByText('WHO GFMD')).toHaveLength(2) // header badge + panel row
    })
  })
})
