/**
 * Tests for TrackDiagnosisPage — AI-powered track health and competitiveness.
 *
 * Covers:
 * 1. Renders the page title and the input prompt
 * 2. Start button is disabled when keyword is empty
 * 3. Empty state appears when no diagnosis has been fetched
 * 4. diagnoseTrack is called with the trimmed keyword
 * 5. Rate-limit check failure prevents the API call
 * 6. Diagnosis result renders health/competitiveness scores and direction advice
 * 7. Sub-tracks render when present
 * 8. Rollback is called when the API returns null
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const {
  diagnoseTrackMock,
  checkAndConsumeMock,
  rollbackMock,
} = vi.hoisted(() => ({
  diagnoseTrackMock: vi.fn(),
  checkAndConsumeMock: vi.fn(() => true),
  rollbackMock: vi.fn(),
}));

vi.mock('@/services/api/tracks', () => ({
  diagnoseTrack: diagnoseTrackMock,
}));
vi.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: () => ({
    remaining: 10,
    usagePercent: 50,
    isLow: false,
    isExhausted: false,
    checkAndConsume: checkAndConsumeMock,
    rollback: rollbackMock,
    rateLimit: {},
    updateRateLimit: vi.fn(),
  }),
}));

import TrackDiagnosisPage from '../TrackDiagnosisPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <TrackDiagnosisPage />
    </MemoryRouter>,
  );
}

describe('TrackDiagnosisPage', () => {
  beforeEach(() => {
    diagnoseTrackMock.mockReset();
    checkAndConsumeMock.mockReset();
    rollbackMock.mockReset();
    checkAndConsumeMock.mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the keyword input', () => {
    renderPage();
    expect(screen.getByText('赛道诊断')).toBeInTheDocument();
    expect(screen.getByText('输入赛道关键词')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/美妆护肤/)).toBeInTheDocument();
  });

  it('disables the start button when the keyword is empty', () => {
    renderPage();
    const button = screen.getByRole('button', { name: '开始诊断' });
    expect(button).toBeDisabled();
  });

  it('enables the start button when the keyword is non-empty', () => {
    renderPage();
    const input = screen.getByPlaceholderText(/美妆护肤/);
    fireEvent.change(input, { target: { value: '美妆' } });
    expect(screen.getByRole('button', { name: '开始诊断' })).not.toBeDisabled();
  });

  it('shows the empty state when no diagnosis has been fetched', () => {
    renderPage();
    expect(screen.getByText('等待赛道关键词')).toBeInTheDocument();
  });

  it('calls diagnoseTrack with the trimmed keyword on click', async () => {
    diagnoseTrackMock.mockResolvedValue({
      data: {
        id: 'd-1',
        track_keyword: '美妆',
        health_score: 0.8,
        competitiveness_score: 0.4,
        sub_tracks: [],
        direction_advice: '关注细分品类',
        data_source: 'heuristic',
        confidence: 0.6,
      },
    });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/美妆护肤/), {
      target: { value: '  美妆  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始诊断' }));

    await waitFor(() => {
      expect(checkAndConsumeMock).toHaveBeenCalled();
      expect(diagnoseTrackMock).toHaveBeenCalledWith({ track_keyword: '美妆' });
    });
  });

  it('does NOT call diagnoseTrack when rate-limit check fails', () => {
    checkAndConsumeMock.mockReturnValue(false);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/美妆护肤/), {
      target: { value: '美妆' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始诊断' }));
    expect(diagnoseTrackMock).not.toHaveBeenCalled();
  });

  it('does NOT call diagnoseTrack when keyword is only whitespace', () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/美妆护肤/), {
      target: { value: '   ' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始诊断' }));
    expect(diagnoseTrackMock).not.toHaveBeenCalled();
  });

  it('renders health + competitiveness scores and direction advice on success', async () => {
    diagnoseTrackMock.mockResolvedValue({
      data: {
        id: 'd-1',
        track_keyword: '美妆',
        health_score: 0.82,
        competitiveness_score: 0.3,
        sub_tracks: [],
        direction_advice: '聚焦敏感肌细分',
        data_source: 'heuristic',
        confidence: 0.7,
      },
    });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/美妆护肤/), {
      target: { value: '美妆' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始诊断' }));

    expect(await screen.findByText('赛道健康度')).toBeInTheDocument();
    expect(screen.getByText('竞争激烈度')).toBeInTheDocument();
    expect(screen.getByText('方向建议')).toBeInTheDocument();
    expect(screen.getByText('聚焦敏感肌细分')).toBeInTheDocument();
  });

  it('renders sub-tracks when the diagnosis includes them', async () => {
    diagnoseTrackMock.mockResolvedValue({
      data: {
        id: 'd-1',
        track_keyword: '美妆',
        health_score: 0.7,
        competitiveness_score: 0.3,
        sub_tracks: [
          { name: '敏感肌护肤', potential_score: 0.8, reason: '蓝海' },
          { name: '成分党', potential_score: 0.5, reason: '红海' },
        ],
        direction_advice: '聚焦细分',
        data_source: 'heuristic',
        confidence: 0.6,
      },
    });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/美妆护肤/), {
      target: { value: '美妆' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始诊断' }));

    expect(await screen.findByText('推荐子赛道')).toBeInTheDocument();
    expect(screen.getByText('敏感肌护肤')).toBeInTheDocument();
    expect(screen.getByText('成分党')).toBeInTheDocument();
  });

  it('calls rollback when the API call returns null', async () => {
    diagnoseTrackMock.mockResolvedValue({ data: null });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/美妆护肤/), {
      target: { value: '美妆' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始诊断' }));

    await waitFor(() => {
      expect(diagnoseTrackMock).toHaveBeenCalled();
      expect(rollbackMock).toHaveBeenCalled();
    });
  });
});
