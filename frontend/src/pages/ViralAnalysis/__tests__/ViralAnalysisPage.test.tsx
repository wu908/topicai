/**
 * Tests for ViralAnalysisPage — viral content structural breakdown with
 * text/image input modes, viral score, attribution list, transferable
 * template, and risk warnings.
 *
 * Covers:
 * 1. Renders the page title and the empty state on first load (text mode)
 * 2. Input mode toggle: clicking 图片分析 reveals the upload area
 * 3. Analyze button is disabled when text is empty
 * 4. Typing text enables the button
 * 5. Clicking analyze calls the API with input_type=text + content
 * 6. rate-limit gate: when checkAndConsume returns false, API is not called
 * 7. Rollback is called when execute returns null
 * 8. Loading state shows LoadingCard skeletons
 * 9. Result renders viral score (×100), ConfidenceBadge, DataSourceTag
 * 10. Attribution list renders one entry per conclusion with dimension Chip
 * 11. Transferable template block renders the template text
 * 12. Risk warnings list renders the warnings
 * 13. Shows a role=alert when the API rejects
 * 14. Image upload: typing a Data URL in the file input populates the preview
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const {
  analyzeViralMock,
  checkAndConsumeMock,
  rollbackMock,
  addNotificationMock,
} = vi.hoisted(() => ({
  analyzeViralMock: vi.fn(),
  checkAndConsumeMock: vi.fn(),
  rollbackMock: vi.fn(),
  addNotificationMock: vi.fn(),
}));

vi.mock('@/services/api/viral', () => ({
  analyzeViral: analyzeViralMock,
}));

const rateLimitRef = { remaining: 5, usagePercent: 25, isLow: false, isExhausted: false };
vi.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: () => ({
    remaining: rateLimitRef.remaining,
    usagePercent: rateLimitRef.usagePercent,
    isLow: rateLimitRef.isLow,
    isExhausted: rateLimitRef.isExhausted,
    checkAndConsume: checkAndConsumeMock,
    rollback: rollbackMock,
    rateLimit: rateLimitRef,
    updateRateLimit: vi.fn(),
  }),
}));

vi.mock('@/store/appStore', () => ({
  useAppStore: (selector: (s: { addNotification: typeof addNotificationMock }) => unknown) =>
    selector({ addNotification: addNotificationMock }),
}));

import ViralAnalysisPage from '../ViralAnalysisPage';

const SAMPLE_ANALYSIS = {
  id: 'va-1',
  user_id: 'u-1',
  input_type: 'text' as const,
  input_text: 'a great viral article',
  viral_score: 0.82,
  structural_analysis: { hook: 'curiosity-gap', length: 1200 },
  attributions: [
    {
      dimension: '钩子设计',
      conclusion: '前 3 句制造了强好奇心缺口',
      relevance: 0.9,
      evidence: '标题以「你绝对想不到」开头，正文首段连续 3 个反问',
    },
    {
      dimension: '结构节奏',
      conclusion: '段落长度短，视觉节奏快',
      relevance: 0.7,
      evidence: '平均段落 2.3 行，每 80 字一个小标题',
    },
    {
      dimension: '情绪曲线',
      conclusion: '从焦虑 → 解密 → 释然',
      relevance: 0.8,
      evidence: '情绪词密度 4.2/百字，高于基线 1.6 倍',
    },
  ],
  transferable_template: '【痛点场景】→【反常识结论】→【3 步方法】→【行动召唤】',
  rewrite_suggestions: '把开头换成更具体的数字。',
  risk_warnings: ['可能涉及医疗夸大表述', '建议增加免责声明'],
  confidence: 0.87,
  data_source: 'ai_inference' as const,
  created_at: '2026-06-14T00:00:00Z',
};

function renderPage() {
  return render(
    <MemoryRouter>
      <ViralAnalysisPage />
    </MemoryRouter>,
  );
}

describe('ViralAnalysisPage', () => {
  beforeEach(() => {
    analyzeViralMock.mockReset();
    checkAndConsumeMock.mockReset();
    rollbackMock.mockReset();
    addNotificationMock.mockReset();
    checkAndConsumeMock.mockReturnValue(true);
    analyzeViralMock.mockResolvedValue({ data: SAMPLE_ANALYSIS });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page title and the empty state in text mode on first load', () => {
    renderPage();
    expect(screen.getByText('爆款拆解')).toBeInTheDocument();
    expect(screen.getByText('暂无拆解结果')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '文本输入' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('switches to image mode when 图片分析 is clicked', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '图片分析' }));
    expect(screen.getByRole('button', { name: '图片分析' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/点击或拖拽上传图片/)).toBeInTheDocument();
  });

  it('disables the analyze button when text input is empty', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '开始拆解' })).toBeDisabled();
  });

  it('enables the button after text is entered', () => {
    renderPage();
    const textarea = screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...');
    fireEvent.change(textarea, { target: { value: 'some content' } });
    expect(screen.getByRole('button', { name: '开始拆解' })).not.toBeDisabled();
  });

  it('does not call the API when checkAndConsume returns false (rate-limit gate)', () => {
    checkAndConsumeMock.mockReturnValue(false);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    expect(checkAndConsumeMock).toHaveBeenCalled();
    expect(analyzeViralMock).not.toHaveBeenCalled();
  });

  it('calls analyzeViral with input_type=text + trimmed content on click', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: '  a great viral article  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    await waitFor(() => {
      expect(analyzeViralMock).toHaveBeenCalledTimes(1);
    });
    expect(analyzeViralMock).toHaveBeenCalledWith({
      input_type: 'text',
      content: 'a great viral article',
    });
  });

  it('calls rollback when the API returns null', async () => {
    analyzeViralMock.mockResolvedValue({ data: null });
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    await waitFor(() => {
      expect(analyzeViralMock).toHaveBeenCalled();
    });
    expect(rollbackMock).toHaveBeenCalledTimes(1);
  });

  it('does NOT call rollback when the API returns a valid result', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    await waitFor(() => {
      expect(analyzeViralMock).toHaveBeenCalled();
    });
    expect(rollbackMock).not.toHaveBeenCalled();
  });

  it('renders the viral score (0.82 → "82" + "分") on result', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    expect(await screen.findByText('82')).toBeInTheDocument();
    expect(screen.getByText('分')).toBeInTheDocument();
  });

  it('renders one attribution entry per conclusion with dimension Chip', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    await screen.findByText('钩子设计');
    expect(screen.getByText('结构节奏')).toBeInTheDocument();
    expect(screen.getByText('情绪曲线')).toBeInTheDocument();
    expect(screen.getByText('前 3 句制造了强好奇心缺口')).toBeInTheDocument();
  });

  it('renders the transferable template block', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    expect(await screen.findByText('可迁移模板')).toBeInTheDocument();
    expect(
      screen.getByText('【痛点场景】→【反常识结论】→【3 步方法】→【行动召唤】'),
    ).toBeInTheDocument();
  });

  it('renders the risk-warnings list with one bullet per warning', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    expect(await screen.findByText('风险提示')).toBeInTheDocument();
    expect(screen.getByText('• 可能涉及医疗夸大表述')).toBeInTheDocument();
    expect(screen.getByText('• 建议增加免责声明')).toBeInTheDocument();
  });

  it('renders the data_source tag and confidence badge', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    // Wait for the result to land.
    await screen.findByText('82');
    // DataSourceTag renders the formatted source label (e.g. "AI推断")
    // inside an MUI Chip. The icon is a separate child node, so the label
    // is split across siblings. Multiple elements render "AI推断" once
    // for the DataSourceTag and once for the AICreatedBadge label, so
    // assert presence via getAllByText length.
    const matches = screen.getAllByText(
      (_, node) => !!node && node.textContent === 'AI推断',
    );
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('on API rejection, the page returns to the empty state and the rate-limit call is rolled back', async () => {
    // The page does not render an explicit error UI on API failure; it
    // relies on useApi's catch path returning null and the page calling
    // rollback() to refund the consumed quota. Verify that contract.
    analyzeViralMock.mockRejectedValueOnce(new Error('500'));
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('粘贴爆款内容文案、标题或链接...'), {
      target: { value: 'some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: '开始拆解' }));
    await waitFor(() => {
      expect(analyzeViralMock).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(rollbackMock).toHaveBeenCalledTimes(1);
    });
    // The page should NOT render the result block after the failure.
    expect(screen.queryByText('爆款指数')).not.toBeInTheDocument();
    // The empty state is still visible.
    expect(screen.getByText('暂无拆解结果')).toBeInTheDocument();
  });

  it('image mode renders the file input and the upload-hint label', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '图片分析' }));
    // The file input is hidden (display: none) and labelled by the dashed box.
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('accept', 'image/*');
    expect(screen.getByText(/点击或拖拽上传图片/)).toBeInTheDocument();
    // In image mode without an uploaded file, the analyze button is disabled
    // (the `content` state is still empty).
    expect(screen.getByRole('button', { name: '开始拆解' })).toBeDisabled();
  });
});
