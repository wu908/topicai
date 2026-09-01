import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const createProject = vi.fn();
const confirmProjectIntent = vi.fn();
vi.mock('@/services/api/v2/projects', () => ({
  createProject: (...a: unknown[]) => createProject(...a),
  confirmProjectIntent: (...a: unknown[]) => confirmProjectIntent(...a),
}));

import UrgentPage from '../UrgentPage';

describe('UrgentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createProject.mockResolvedValue({ id: 'p1', version: 1, title: '' });
    confirmProjectIntent.mockResolvedValue({});
  });

  it('creates project without intent when left empty', async () => {
    render(<MemoryRouter><UrgentPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('标题'), { target: { value: '阳台辣椒结果了' } });
    fireEvent.change(screen.getByLabelText('真实经历'), { target: { value: '早上浇水时发现了三个果。' } });
    fireEvent.click(screen.getByText('创建并进入内容工作台'));
    await waitFor(() => expect(createProject).toHaveBeenCalled());
    const call = createProject.mock.calls[0][0];
    expect(call.title).toBe('阳台辣椒结果了');
    expect(call.content_intent).toBeUndefined();
    expect(confirmProjectIntent).not.toHaveBeenCalled();
  });

  it('confirms intent when selected and navigates to workspace', async () => {
    render(
      <MemoryRouter initialEntries={['/urgent']}>
        <Routes>
          <Route path="/urgent" element={<UrgentPage />} />
          <Route path="/content/:projectId" element={<div>工作台 p1</div>} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText('标题'), { target: { value: '阳台辣椒结果了' } });
    fireEvent.change(screen.getByLabelText('真实经历'), { target: { value: '早上浇水时发现了三个果。' } });
    // 意图选择
    const select = screen.getByLabelText(/意图/);
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByText('记录 · 记下这个变化'));
    fireEvent.click(screen.getByText('创建并进入内容工作台'));
    await waitFor(() => expect(confirmProjectIntent).toHaveBeenCalled());
    expect(await screen.findByText('工作台 p1')).toBeTruthy();
  });

  it('disables submit until title and experience present', () => {
    render(<MemoryRouter><UrgentPage /></MemoryRouter>);
    expect((screen.getByText('创建并进入内容工作台') as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(screen.getByLabelText('标题'), { target: { value: 't' } });
    fireEvent.change(screen.getByLabelText('真实经历'), { target: { value: 'e' } });
    expect((screen.getByText('创建并进入内容工作台') as HTMLButtonElement).disabled).toBe(false);
  });
});
