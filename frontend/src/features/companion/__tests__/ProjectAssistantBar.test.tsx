import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import ProjectAssistantBar from '../ProjectAssistantBar';

/** 与 aiIdentity.ts 里的 KEY 一致：组件只通过 localStorage 读身份。 */
const IDENTITY_KEY = 'topicai.ai-identities.v1';

const seedProjectIdentity = (project: Record<string, unknown>) => {
  window.localStorage.setItem(IDENTITY_KEY, JSON.stringify({ project }));
};

const readProjectIdentity = () =>
  JSON.parse(window.localStorage.getItem(IDENTITY_KEY) ?? '{}').project as {
    name?: string;
    avatar?: string | null;
    tone?: string;
  };

const avatarDivs = () =>
  Array.from(document.querySelectorAll<HTMLDivElement>('div[aria-hidden="true"]'));

const openEditor = () =>
  fireEvent.click(screen.getByRole('button', { name: '自定义项目助手' }));

describe('ProjectAssistantBar', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('shows the project assistant and says it only handles this one piece of content', () => {
    render(<ProjectAssistantBar />);

    expect(screen.getByText('项目助手')).toBeInTheDocument();
    expect(screen.getByText('项目助手 · 只处理这一条内容')).toBeInTheDocument();
    // 没有头像时用名字首字兜底，避免出现空圆
    expect(avatarDivs()[0]).toHaveTextContent('项');
    expect(avatarDivs()[0]?.style.backgroundImage).toContain('radial-gradient');
  });

  it('paints a custom avatar image instead of resetting it to a blank circle', () => {
    seedProjectIdentity({
      name: '小七',
      avatar: 'data:image/png;base64,iVBORw0KGgo=',
      tone: 'a',
    });
    render(<ProjectAssistantBar />);

    const avatar = avatarDivs()[0];
    // background-image 必须留在元素上：background 简写写在后面会把它清掉。
    expect(avatar.style.backgroundImage).toContain('data:image/png');
    expect(avatar).not.toHaveTextContent('小');
  });

  it('names the project scope in the subtitle when a project is open', () => {
    render(<ProjectAssistantBar projectName="一个特别长的项目名字超出十个字" />);

    expect(screen.getByText(/项目助手 · 只处理「一个特别长的项目名字…」/)).toBeInTheDocument();
  });

  it('keeps a short project name intact without a trailing ellipsis', () => {
    render(<ProjectAssistantBar projectName="阳台种菜" />);

    expect(screen.getByText('项目助手 · 只处理「阳台种菜」')).toBeInTheDocument();
    expect(screen.queryByText(/阳台种菜…/)).not.toBeInTheDocument();
  });

  it('renames the project assistant from the edit popover and persists it', async () => {
    render(<ProjectAssistantBar />);

    openEditor();
    expect(await screen.findByText('项目助手外观')).toBeInTheDocument();
    expect(screen.getByText('与全局 AI 分开保存，避免认错人。')).toBeInTheDocument();

    const nameInput = screen.getByLabelText('名称');
    fireEvent.change(nameInput, { target: { value: '写作搭子' } });
    fireEvent.blur(nameInput);

    expect(screen.getByText('写作搭子')).toBeInTheDocument();
    expect(readProjectIdentity().name).toBe('写作搭子');
  });

  it('truncates over-long names and falls back to 项目助手 for a blank one', async () => {
    render(<ProjectAssistantBar />);
    openEditor();
    const nameInput = await screen.findByLabelText('名称');

    fireEvent.change(nameInput, { target: { value: 'abcdefghijklmnop' } });
    fireEvent.blur(nameInput);
    expect(readProjectIdentity().name).toBe('abcdefghijkl');

    fireEvent.change(nameInput, { target: { value: '   ' } });
    fireEvent.blur(nameInput);
    expect(readProjectIdentity().name).toBe('项目助手');
    expect(screen.getAllByText('项目助手').length).toBeGreaterThan(0);
  });

  it('resets a custom avatar back to the default gradient', async () => {
    seedProjectIdentity({
      name: '小七',
      avatar: 'data:image/png;base64,iVBORw0KGgo=',
      tone: 'a',
    });
    render(<ProjectAssistantBar />);

    // 有自定义头像时不再用名字首字兜底
    expect(screen.getByText('小七')).toBeInTheDocument();
    expect(avatarDivs()[0]).toHaveTextContent('');

    openEditor();
    fireEvent.click(await screen.findByRole('button', { name: '用默认' }));

    expect(readProjectIdentity()).toEqual({ name: '小七', avatar: null, tone: 'c' });
    expect(avatarDivs()[0]).toHaveTextContent('小');
  });

  it('stores an uploaded file as a data URL avatar', async () => {
    render(<ProjectAssistantBar />);
    openEditor();
    await screen.findByText('项目助手外观');

    const fileInput = document.querySelector<HTMLInputElement>('input[type="file"]');
    expect(fileInput).not.toBeNull();
    const file = new File(['avatar-bytes'], 'me.png', { type: 'image/png' });
    fireEvent.change(fileInput!, { target: { files: [file] } });

    await waitFor(() => {
      expect(readProjectIdentity().avatar).toMatch(/^data:image\/png;base64,/);
    });
  });

  it('follows identity changes saved in another tab', () => {
    render(<ProjectAssistantBar />);
    expect(screen.getByText('项目助手')).toBeInTheDocument();

    seedProjectIdentity({ name: '另一个助手' });
    fireEvent(window, new Event('storage'));

    expect(screen.getByText('另一个助手')).toBeInTheDocument();
  });

  it('closes the appearance popover from 完成', async () => {
    render(<ProjectAssistantBar />);
    openEditor();
    await screen.findByText('项目助手外观');

    fireEvent.click(screen.getByRole('button', { name: '完成' }));

    await waitFor(() =>
      expect(screen.queryByText('项目助手外观')).not.toBeInTheDocument(),
    );
  });
});
