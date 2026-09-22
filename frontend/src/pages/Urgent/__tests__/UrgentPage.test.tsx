import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const createProject = vi.fn();
const confirmProjectIntent = vi.fn();
const getProjectNextAction = vi.fn();
const respondToAction = vi.fn();
const startProject = vi.fn();
vi.mock('@/services/api/v2/projects', () => ({
  createProject: (...a: unknown[]) => createProject(...a),
  confirmProjectIntent: (...a: unknown[]) => confirmProjectIntent(...a),
  getProjectNextAction: (...a: unknown[]) => getProjectNextAction(...a),
  respondToAction: (...a: unknown[]) => respondToAction(...a),
  startProject: (...a: unknown[]) => startProject(...a),
}));

import UrgentPage from '../UrgentPage';

/** 工作台替身：把导航 state 里的推断结果摊开，验证它真的被带过去了。 */
function Workspace() {
  const location = useLocation();
  const state = location.state as { inference?: { intent_label?: string } } | null;
  return <div>工作台 p1 · 推断：{state?.inference?.intent_label ?? '无'}</div>;
}

const SUBMIT = '开始准备候选内容';

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/urgent']}>
      <Routes>
        <Route path="/urgent" element={<UrgentPage />} />
        <Route path="/content/:projectId" element={<Workspace />} />
      </Routes>
    </MemoryRouter>,
  );
}

function fill() {
  fireEvent.change(screen.getByLabelText('这篇想说什么？'), {
    target: { value: '阳台辣椒结果了' },
  });
  fireEvent.change(screen.getByLabelText('一句真实经历（它只基于这个写，不编）'), {
    target: { value: '早上浇水时发现了三个果。' },
  });
}

describe('UrgentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createProject.mockResolvedValue({ id: 'p1', version: 1, title: '' });
    confirmProjectIntent.mockResolvedValue({});
    getProjectNextAction.mockResolvedValue({
      id: 'a1',
      action_type: 'answer_key_question',
      version: 1,
    });
    respondToAction.mockResolvedValue({});
    startProject.mockResolvedValue({
      project_id: 'p1',
      title: '阳台辣椒结果了',
      material_id: 'm1',
      inference: {
        intent: 'record',
        intent_label: '记过程',
        reason: '你在讲一件刚发生的事',
        confidence: 'high',
        next_question: '你还记得当时的细节吗',
        source: 'ai',
      },
    });
  });

  // F1（用户验收测试 2026-09-19）：页面原先写「三步，十分钟内见成品」，
  // 但本页交付的是「一个已确认意图的项目」，成品要再经过候选内容与发布前检查。
  it('不再承诺十分钟交付成品', () => {
    renderPage();
    expect(screen.queryByText(/十分钟内见成品/)).toBeNull();
    expect(screen.getByText(/三步写下真实经历/)).toBeTruthy();
  });

  // F1 的另一半：选「让它判断」以前只 createProject、从不确认意图，
  // 用户落地在 0/5 步——「交给 AI 判断」反而比明确选一个更差。
  it('选「让它判断」时走 AI 推断，并把推断结果带进工作台', async () => {
    renderPage();
    fill();
    fireEvent.click(screen.getByText(SUBMIT));

    await waitFor(() => expect(startProject).toHaveBeenCalled());
    expect(createProject).not.toHaveBeenCalled();
    const call = startProject.mock.calls[0][0];
    expect(call.raw_input).toContain('阳台辣椒结果了');
    expect(call.raw_input).toContain('早上浇水时发现了三个果。');
    expect(call.idempotency_key).toBeTruthy();

    expect(await screen.findByText(/推断：记过程/)).toBeTruthy();
  });

  it('明确选了意图时确认意图并回填经历，再进工作台', async () => {
    renderPage();
    fill();
    fireEvent.click(screen.getByRole('button', { name: '记过程' }));
    fireEvent.click(screen.getByText(SUBMIT));

    await waitFor(() => expect(confirmProjectIntent).toHaveBeenCalled());
    expect(startProject).not.toHaveBeenCalled();
    expect(createProject.mock.calls[0][0].content_intent).toBe('record');
    await waitFor(() =>
      expect(respondToAction).toHaveBeenCalledWith(
        'a1',
        expect.objectContaining({
          decision: 'accept',
          response_payload: { answer: '早上浇水时发现了三个果。' },
        }),
      ),
    );
    expect(await screen.findByText('工作台 p1 · 推断：无')).toBeTruthy();
  });

  it('disables submit until title and experience present', () => {
    renderPage();
    expect((screen.getByText(SUBMIT) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(screen.getByLabelText('这篇想说什么？'), { target: { value: 't' } });
    fireEvent.change(screen.getByLabelText('一句真实经历（它只基于这个写，不编）'), {
      target: { value: 'e' },
    });
    expect((screen.getByText(SUBMIT) as HTMLButtonElement).disabled).toBe(false);
  });
});

// UX 审计 B1：第 2 步的经历要直接变成关键问题的回答，不再重复问一遍。
it('backfills the urgent experience as the key-question answer (B1)', async () => {
  vi.clearAllMocks();
  createProject.mockResolvedValue({ id: 'p1', version: 1, title: '' });
  confirmProjectIntent.mockResolvedValue({});
  getProjectNextAction.mockResolvedValue({
    id: 'a1',
    action_type: 'answer_key_question',
    version: 1,
  });
  respondToAction.mockResolvedValue({});

  renderPage();
  fill();
  fireEvent.click(screen.getByRole('button', { name: '记过程' }));
  fireEvent.click(screen.getByText(SUBMIT));

  await waitFor(() =>
    expect(respondToAction).toHaveBeenCalledWith(
      'a1',
      expect.objectContaining({
        decision: 'accept',
        response_payload: { answer: '早上浇水时发现了三个果。' },
      }),
    ),
  );
});

it('still navigates when the experience backfill fails (B1 non-blocking)', async () => {
  vi.clearAllMocks();
  createProject.mockResolvedValue({ id: 'p1', version: 1, title: '' });
  confirmProjectIntent.mockResolvedValue({});
  getProjectNextAction.mockRejectedValue(new Error('network down'));

  renderPage();
  fill();
  fireEvent.click(screen.getByRole('button', { name: '记过程' }));
  fireEvent.click(screen.getByText(SUBMIT));

  await waitFor(() => expect(screen.getByText('工作台 p1 · 推断：无')).toBeTruthy());
});
