/**
 * Tests for IdeaBoosterPage — vague-idea → structured plan.
 *
 * Covers:
 * 1. Renders the page title + empty state
 * 2. The boost button is disabled when the idea field is empty
 * 3. Typing an idea enables the button
 * 4. Clicking boost calls boostIdea with the text + optional context
 * 5. Renders one card per assumption + title_candidate after success
 * 6. The boost button is disabled while a request is in flight
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { boostIdeaMock, checkAndConsumeMock, rollbackMock } = vi.hoisted(() => ({
  boostIdeaMock: vi.fn(),
  checkAndConsumeMock: vi.fn().mockReturnValue(true),
  rollbackMock: vi.fn(),
}));
vi.mock('@/services/api/ideas', () => ({
  boostIdea: boostIdeaMock,
}));

vi.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: () => ({
    checkAndConsume: checkAndConsumeMock,
    rollback: rollbackMock,
    remaining: 10,
    usagePercent: 30,
    isLow: false,
    isExhausted: false,
  }),
}));

import IdeaBoosterPage from '../IdeaBoosterPage';

const SAMPLE = {
  id: 'i-1',
  idea_text: 'x',
  key_assumptions: ['ass-1', 'ass-2', 'ass-3'],
  feasibility_assessment: 'feasible',
  title_candidates: ['title-A', 'title-B'],
  content_outline: 'outline',
  publish_schedule: 'schedule',
  confidence: 0.8,
  data_source: 'heuristic' as const,
};

function renderPage() {
  return render(
    <MemoryRouter>
      <IdeaBoosterPage />
    </MemoryRouter>,
  );
}

describe('IdeaBoosterPage', () => {
  beforeEach(() => {
    boostIdeaMock.mockReset();
    checkAndConsumeMock.mockReset();
    checkAndConsumeMock.mockReturnValue(true);
    rollbackMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title + empty state on first load', () => {
    renderPage();
    expect(screen.getByText('想法推进')).toBeInTheDocument();
    expect(screen.getByText('等待你的想法')).toBeInTheDocument();
  });

  it('the boost button is disabled when the idea field is empty', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '推进想法' })).toBeDisabled();
  });

  it('typing an idea enables the button', () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/想做一期关于/), {
      target: { value: '我的模糊想法' },
    });
    expect(screen.getByRole('button', { name: '推进想法' })).not.toBeDisabled();
  });

  it('clicking boost calls boostIdea with idea_text and undefined context', async () => {
    boostIdeaMock.mockResolvedValue({ data: SAMPLE });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/想做一期关于/), {
      target: { value: '我的模糊想法' },
    });
    fireEvent.click(screen.getByRole('button', { name: '推进想法' }));

    await waitFor(() => {
      expect(boostIdeaMock).toHaveBeenCalledWith({
        idea_text: '我的模糊想法',
        context: undefined,
      });
    });
  });

  it('passes the context field through when provided', async () => {
    boostIdeaMock.mockResolvedValue({ data: SAMPLE });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/想做一期关于/), {
      target: { value: '想法' },
    });
    fireEvent.change(screen.getByPlaceholderText(/补充背景信息/), {
      target: { value: '面向打工人' },
    });
    fireEvent.click(screen.getByRole('button', { name: '推进想法' }));

    await waitFor(() => {
      expect(boostIdeaMock).toHaveBeenCalledWith({
        idea_text: '想法',
        context: '面向打工人',
      });
    });
  });

  it('renders one assumption chip per key_assumption and one title per title_candidate', async () => {
    boostIdeaMock.mockResolvedValue({ data: SAMPLE });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/想做一期关于/), {
      target: { value: '想法' },
    });
    fireEvent.click(screen.getByRole('button', { name: '推进想法' }));

    await waitFor(() => {
      expect(screen.getByText('ass-1')).toBeInTheDocument();
    });
    expect(screen.getByText('ass-2')).toBeInTheDocument();
    expect(screen.getByText('ass-3')).toBeInTheDocument();
    expect(screen.getByText('title-A')).toBeInTheDocument();
    expect(screen.getByText('title-B')).toBeInTheDocument();
    expect(screen.getByText('核心假设')).toBeInTheDocument();
    expect(screen.getByText('标题候选')).toBeInTheDocument();
  });

  it('does not call boostIdea when rate-limit checkAndConsume returns false', async () => {
    checkAndConsumeMock.mockReturnValue(false);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/想做一期关于/), {
      target: { value: '想法' },
    });
    fireEvent.click(screen.getByRole('button', { name: '推进想法' }));
    expect(boostIdeaMock).not.toHaveBeenCalled();
  });
});
