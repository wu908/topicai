import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('gsap', () => ({
  gsap: {
    set: vi.fn(),
    timeline: vi.fn(() => {
      const tl = {
        addLabel: vi.fn(() => tl),
        to: vi.fn(() => tl),
      };
      return tl;
    }),
  },
}));

const { askCompanionMock } = vi.hoisted(() => ({
  askCompanionMock: vi.fn(),
}));

vi.mock('@/services/api/v2/companion', () => ({
  askCompanion: askCompanionMock,
}));

import CompanionDialog from '../CompanionDialog';
import { openCompanion } from '../openCompanion';

describe('CompanionDialog', () => {
  beforeEach(() => {
    sessionStorage.clear();
    askCompanionMock.mockReset();
  });

  it('renders the orb and opens with a greeting on click', async () => {
    render(<CompanionDialog />);
    const orb = screen.getByRole('button', { name: '对话悬浮球' });
    expect(orb).toBeTruthy();
    fireEvent.click(orb);
    expect(screen.getAllByText(/全局/).length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText('问它，或说你的想法…')).toBeTruthy();
  });

  it('injects context via openCompanion and shows it as the chip', async () => {
    render(<CompanionDialog />);
    openCompanion('产出架 · 阳台种菜 30 天');
    expect(await screen.findByText('产出架 · 阳台种菜 30 天')).toBeTruthy();
    expect(screen.getByText(/就「产出架 · 阳台种菜 30 天」聊两句/)).toBeTruthy();
  });

  it('sends a user bubble and renders the real model answer', async () => {
    askCompanionMock.mockResolvedValue({
      code: 200,
      data: { answer: '先把这条素材拾取下来，再观察 7 天。' },
      message: 'success',
      meta: {},
    });
    render(<CompanionDialog />);
    fireEvent.click(screen.getByRole('button', { name: '对话悬浮球' }));
    const input = await screen.findByPlaceholderText('问它，或说你的想法…');
    fireEvent.change(input, { target: { value: '为什么先用语音而不是照片？' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(screen.getByText('为什么先用语音而不是照片？')).toBeTruthy();
    expect(await screen.findByText('先把这条素材拾取下来，再观察 7 天。')).toBeTruthy();
    expect(askCompanionMock).toHaveBeenCalledWith(
      expect.objectContaining({ question: '为什么先用语音而不是照片？' }),
    );
    // 罐头演示回复必须绝迹。
    expect(screen.queryByText(/演示回复/)).toBeNull();
  });

  it('surfaces an honest error instead of a canned reply when AI fails', async () => {
    askCompanionMock.mockRejectedValue(new Error('AI 服务不可用'));
    render(<CompanionDialog />);
    fireEvent.click(screen.getByRole('button', { name: '对话悬浮球' }));
    const input = await screen.findByPlaceholderText('问它，或说你的想法…');
    fireEvent.change(input, { target: { value: '在吗' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(await screen.findByText('AI 服务不可用')).toBeTruthy();
  });

  it('toggles zen fading of chrome, keeps bubbles visible', async () => {
    render(<CompanionDialog />);
    fireEvent.click(screen.getByRole('button', { name: '对话悬浮球' }));
    const zen = await screen.findByRole('button', { name: '渐隐' });
    fireEvent.click(zen);
    expect(screen.getByRole('button', { name: '唤醒' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: '唤醒' }));
    expect(screen.getByRole('button', { name: '渐隐' })).toBeTruthy();
  });

  it('closes on the close button and reopens via orb', async () => {
    render(<CompanionDialog />);
    fireEvent.click(screen.getByRole('button', { name: '对话悬浮球' }));
    const close = await screen.findByRole('button', { name: '关闭' });
    fireEvent.click(close);
    await waitFor(() => expect(screen.queryByPlaceholderText('问它，或说你的想法…')).toBeNull());
    fireEvent.click(screen.getByRole('button', { name: '对话悬浮球' }));
    expect(await screen.findByPlaceholderText('问它，或说你的想法…')).toBeTruthy();
  });
});
