import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { askCompanionMock } = vi.hoisted(() => ({
  askCompanionMock: vi.fn(),
}));

vi.mock('@/services/api/v2/companion', () => ({
  askCompanion: askCompanionMock,
}));

import GlobalAIPanel from '../GlobalAIPanel';
import { defaultIdentities, notifyIdentities, updateIdentity } from '../aiIdentity';

const INPUT_PLACEHOLDER = '记一条灵感，或让我帮你操作（如：把番茄钟标为待对账）…';
const IDENTITY_KEY = 'topicai.ai-identities.v1';

const openPanel = () => fireEvent.click(screen.getByRole('button', { name: '打开全局 AI' }));

const typeAndEnter = (text: string) => {
  const input = screen.getByPlaceholderText(INPUT_PLACEHOLDER);
  fireEvent.change(input, { target: { value: text } });
  fireEvent.keyDown(input, { key: 'Enter' });
};

describe('GlobalAIPanel', () => {
  beforeEach(() => {
    localStorage.clear();
    askCompanionMock.mockReset();
    askCompanionMock.mockResolvedValue({
      code: 200,
      data: { answer: '先说清要什么，我帮你记进「想发的」。' },
      message: 'ok',
      meta: {},
    });
  });

  it('starts closed and opens from the floating ball', () => {
    render(<GlobalAIPanel />);

    const panel = screen.getByLabelText('全局 AI 助手');
    expect(panel).toHaveClass('ai-panel');
    expect(panel).not.toHaveClass('open');
    expect(panel).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByText('我是全局助手')).toBeInTheDocument();

    openPanel();

    expect(panel).toHaveClass('open');
    expect(panel).toHaveAttribute('aria-hidden', 'false');
    expect(screen.getByLabelText('AI 名称')).toHaveTextContent('阿洛');
    expect(screen.getByText(/灵感速记/)).toBeInTheDocument();
    expect(screen.getByText(/全局操控/)).toBeInTheDocument();
  });

  it('keeps the closed panel out of the tab order with inert', () => {
    render(<GlobalAIPanel />);
    const panel = screen.getByLabelText('全局 AI 助手');

    expect(panel).toHaveAttribute('inert');
    openPanel();
    expect(panel).not.toHaveAttribute('inert');
  });

  it('answers the attachment and rename buttons instead of doing nothing', () => {
    render(<GlobalAIPanel />);
    openPanel();

    fireEvent.click(screen.getByRole('button', { name: /附件/ }));
    expect(screen.getByText(/附件还在开发中/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '改名字' }));
    expect(screen.getByText(/名称和头像请到左侧「设置 · 全局 AI」里改/)).toBeInTheDocument();
  });

  it('toggles with Alt+Space and closes on Escape', () => {
    render(<GlobalAIPanel />);
    const panel = screen.getByLabelText('全局 AI 助手');

    fireEvent.keyDown(window, { key: ' ', code: 'Space', altKey: true });
    expect(panel).toHaveClass('open');

    fireEvent.keyDown(window, { key: ' ', code: 'Space', altKey: true });
    expect(panel).not.toHaveClass('open');

    openPanel();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(panel).not.toHaveClass('open');
  });

  it('closes from the close button after it is open', () => {
    render(<GlobalAIPanel />);
    openPanel();

    fireEvent.click(screen.getByRole('button', { name: '关闭' }));

    expect(screen.getByLabelText('全局 AI 助手')).not.toHaveClass('open');
  });

  it('sends a note to the global assistant and renders the real answer', async () => {
    render(<GlobalAIPanel />);
    openPanel();

    typeAndEnter('把「番茄钟」标为待对账');

    expect(screen.getByText('把「番茄钟」标为待对账')).toBeInTheDocument();
    expect(await screen.findByText('先说清要什么，我帮你记进「想发的」。')).toBeInTheDocument();
    expect(askCompanionMock).toHaveBeenCalledWith({
      context: expect.stringContaining('身份：全局助手'),
      question: '把「番茄钟」标为待对账',
    });
    // 发送后输入框清空。
    expect(screen.getByPlaceholderText(INPUT_PLACEHOLDER)).toHaveValue('');
  });

  it('ignores a whitespace-only draft', () => {
    render(<GlobalAIPanel />);
    openPanel();

    typeAndEnter('   ');

    expect(askCompanionMock).not.toHaveBeenCalled();
    expect(screen.getByText('我是全局助手')).toBeInTheDocument();
  });

  it('falls back to an honest message when the model returns nothing', async () => {
    askCompanionMock.mockResolvedValue({ code: 200, data: { answer: '' }, message: 'ok', meta: {} });
    render(<GlobalAIPanel />);
    openPanel();

    typeAndEnter('在吗');

    expect(
      await screen.findByText('暂时没有答复。你可以再说一句，或点侧栏「设置」检查模型接口。'),
    ).toBeInTheDocument();
  });

  it('surfaces a model failure instead of a canned reply', async () => {
    askCompanionMock.mockRejectedValue(new Error('模型炸了'));
    render(<GlobalAIPanel />);
    openPanel();

    typeAndEnter('在吗');

    expect(await screen.findByText('模型炸了')).toBeInTheDocument();
  });

  it('keeps the voice shortcut honest about being unfinished', () => {
    render(<GlobalAIPanel />);
    openPanel();

    fireEvent.click(screen.getByRole('button', { name: '语音' }));

    expect(
      screen.getByText('语音录入在开发中。你现在可以打字记灵感，或说「立成一条内容」。'),
    ).toBeInTheDocument();
    expect(screen.queryByText('我是全局助手')).toBeNull();
    // 附件与改名入口仍在（改名只在侧栏设置里生效，这里只保留入口）。
    expect(screen.getByRole('button', { name: '＋ 附件' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '改名字' })).toBeInTheDocument();
  });

  it('shows the saved global identity and follows identity changes', async () => {
    localStorage.setItem(
      IDENTITY_KEY,
      JSON.stringify({
        global: { name: '小助手', avatar: null, tone: 'b' },
        project: defaultIdentities.project,
      }),
    );
    render(<GlobalAIPanel />);
    openPanel();

    expect(screen.getByLabelText('AI 名称')).toHaveTextContent('小助手');

    act(() => {
      updateIdentity('global', { name: '新名字' });
      notifyIdentities();
    });

    await waitFor(() => expect(screen.getByLabelText('AI 名称')).toHaveTextContent('新名字'));
  });

  it('falls back to the default identity when storage is malformed', () => {
    localStorage.setItem(IDENTITY_KEY, '{not-json');
    render(<GlobalAIPanel />);
    openPanel();

    expect(screen.getByLabelText('AI 名称')).toHaveTextContent('阿洛');
  });

  it('renders avatar images when the identity has one', () => {
    localStorage.setItem(
      IDENTITY_KEY,
      JSON.stringify({
        global: { name: '小助手', avatar: 'data:image/png;base64,abc', tone: 'a' },
        project: defaultIdentities.project,
      }),
    );
    render(<GlobalAIPanel />);
    openPanel();

    const avatar = document.querySelector('.ai-avatar') as HTMLElement;
    expect(avatar.style.backgroundImage).toContain('data:image/png;base64,abc');
    expect(avatar).toHaveTextContent('');
  });
});
