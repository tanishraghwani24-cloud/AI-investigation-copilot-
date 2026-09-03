/// <reference types="@testing-library/jest-dom" />
import { render, screen } from '@testing-library/react';
import InvestigationDetailPage from '../app/investigations/[id]/page';
import { AgentStatus, CurrentStage } from '@/types';

// Mock fetch globally
global.fetch = jest.fn();

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      refresh: jest.fn(),
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    };
  }
}));

const mockInvestigation = {
  case_id: 'CASE-TEST-001',
  current_stage: CurrentStage.CONTEXT,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  errors: [],
  case_input: {
    customer_profile: {
      customer_id: 'CUST-001',
      name: 'John Doe',
      risk_rating: 'HIGH',
      email: 'john@example.com',
      occupation: 'Developer',
      nationality: 'US'
    },
    transactions: [],
    alert_reason: 'Suspicious activity detected',
  },
  context_intelligence: {
    status: AgentStatus.COMPLETED,
    context_summary: 'This is a test context summary.',
    key_indicators: ['Indicator 1', 'Indicator 2'],
    anomalies: [
      { anomaly_id: 'A1', description: 'Large transfer', severity: 'HIGH' }
    ],
    risk_score: 0.8
  },
  investigation_reasoning: {
    status: AgentStatus.COMPLETED,
    reasoning_summary: 'Test reasoning',
    hypotheses: [
      {
        hypothesis_id: 'H1',
        title: 'Money Laundering',
        confidence: 0.9,
        description: 'High risk',
        supporting_evidence: ['A1'],
        contradicting_evidence: []
      }
    ]
  },
  evidence_compliance_validation: {
    status: AgentStatus.COMPLETED,
    validation_summary: 'All clear',
    compliance_mappings: [
      {
        regulation_id: 'REG-1',
        regulation_name: 'AML',
        is_violated: false,
        evidence_references: [],
        evidence_gaps: []
      }
    ]
  }
};

describe('InvestigationDetailPage', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('renders error state when fetch fails', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found'
    });

    const params = Promise.resolve({ id: 'UNKNOWN' });
    const Component = await InvestigationDetailPage({ params });
    render(Component);

    expect(screen.getByText('Investigation Error')).toBeInTheDocument();
    expect(screen.getByText('No investigation found with ID: UNKNOWN')).toBeInTheDocument();
  });

  it('renders investigation details when fetch succeeds', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockInvestigation
    });

    const params = Promise.resolve({ id: 'CASE-TEST-001' });
    const Component = await InvestigationDetailPage({ params });
    render(Component);

    // Verify route ID was used in fetch
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('CASE-TEST-001'),
      expect.any(Object)
    );

    // Header info
    expect(screen.getByText('CASE-TEST-001')).toBeInTheDocument();
    expect(screen.getAllByText(/John Doe/).length).toBeGreaterThan(0);

    // Context Panel — "Context Intelligence" also appears as a stage label
    // in the InvestigationPipeline execution graph, so it's expected to
    // match more than once (same idiom as the "John Doe" assertion above).
    expect(screen.getAllByText('Context Intelligence').length).toBeGreaterThan(0);
    expect(screen.getByText('This is a test context summary.')).toBeInTheDocument();
    expect(screen.getByText('Indicator 1')).toBeInTheDocument();

    // Reasoning Panel — "Investigation Reasoning" also appears as a stage
    // label in the InvestigationPipeline execution graph.
    expect(screen.getAllByText('Investigation Reasoning').length).toBeGreaterThan(0);
    expect(screen.getByText('Test reasoning')).toBeInTheDocument();
    expect(screen.getByText('Money Laundering')).toBeInTheDocument();

    // Compliance Panel
    expect(screen.getByText('Evidence & Compliance Validation')).toBeInTheDocument();
    expect(screen.getByText('All clear')).toBeInTheDocument();
    expect(screen.getByText('AML')).toBeInTheDocument();
  });

  it('renders empty states when optional data is missing', async () => {
    const emptyMock = {
      ...mockInvestigation,
      context_intelligence: null,
      investigation_reasoning: null,
      evidence_compliance_validation: null,
      decision_optimization: null,
      investigation_report: null
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => emptyMock
    });

    const params = Promise.resolve({ id: 'CASE-TEST-EMPTY' });
    const Component = await InvestigationDetailPage({ params });
    render(Component);

    expect(screen.getByText('No context available')).toBeInTheDocument();
    expect(screen.getByText('No reasoning available')).toBeInTheDocument();
    expect(screen.getByText('No compliance findings')).toBeInTheDocument();
  });
});
