import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listMaterials = vi.fn();
const listProjects = vi.fn();
const createMaterial = vi.fn();
const addMaterialUsage = vi.fn();
const deleteMaterial = vi.fn();

vi.mock('@/services/api/v2/projects', () => ({
  listMaterials: (...args: unknown[]) => listMaterials(...args),
  listProjects: (...args: unknown[]) => listProjects(...args),
  createMaterial: (...args: unknown[]) => createMaterial(...args),
  addMaterialUsage: (...args: unknown[]) => addMaterialUsage(...args),
  deleteMaterial: (...args: unknown[]) => deleteMaterial(...args),
}));

import MaterialsPage from '../MaterialsPage';

describe('MaterialsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listProjects.mockResolvedValue({
      items: [{ id: 'p1', title: '一次真实调整', status: 'preparing' }],
      total: 1,
    });
    listMaterials.mockResolvedValue({
      items: [{
        id: 'm1', title: '失败现场', kind: 'text', mime_type: 'text/plain', size: 12,
        content: '一次真实失败', privacy_level: 'private', version: 1,
        usages: [{ id: 'u1', project_id: 'p1', project_title: '一次真实调整', used_at: '2026-08-06T00:00:00Z' }],
        created_at: '2026-08-06T00:00:00Z', updated_at: '2026-08-06T00:00:00Z',
      }],
      total: 1,
    });
    createMaterial.mockResolvedValue({ id: 'm2' });
    addMaterialUsage.mockResolvedValue({ id: 'm1' });
    deleteMaterial.mockResolvedValue({});
  });

  it('lists reusable materials with privacy and project usages', async () => {
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    expect(await screen.findByText('失败现场')).toBeInTheDocument();
    expect(screen.getByText('私密')).toBeInTheDocument();
    expect(screen.getByText(/一次真实调整/)).toBeInTheDocument();
  });

  it('reuses the idempotency key when saving a material fails and is retried', async () => {
    createMaterial.mockRejectedValueOnce(new Error('network'));
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    await screen.findByText('失败现场');
    fireEvent.click(screen.getByRole('button', { name: '添加素材' }));
    fireEvent.change(screen.getByLabelText(/素材标题/), { target: { value: '方法复盘' } });
    fireEvent.change(screen.getByLabelText(/素材内容/), { target: { value: '具体复盘内容' } });

    // Audit e54a2643: retrying a failed save with a fresh key defeats
    // server-side de-duplication and can create duplicate materials.
    fireEvent.click(screen.getByRole('button', { name: '保存素材' }));
    await waitFor(() => expect(createMaterial).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: '保存素材' }));
    await waitFor(() => expect(createMaterial).toHaveBeenCalledTimes(2));
    expect(createMaterial.mock.calls[1][0].idempotency_key)
      .toBe(createMaterial.mock.calls[0][0].idempotency_key);
  });

  it('creates a text material and links it to a project', async () => {
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    await screen.findByText('失败现场');
    fireEvent.click(screen.getByRole('button', { name: '添加素材' }));
    fireEvent.change(screen.getByLabelText(/素材标题/), { target: { value: '方法复盘' } });
    fireEvent.change(screen.getByLabelText(/素材内容/), { target: { value: '具体复盘内容' } });
    fireEvent.mouseDown(screen.getByLabelText('关联项目'));
    fireEvent.click(screen.getByRole('option', { name: '一次真实调整' }));
    fireEvent.click(screen.getByRole('button', { name: '保存素材' }));

    await waitFor(() => expect(createMaterial).toHaveBeenCalledWith(expect.objectContaining({
      kind: 'text', title: '方法复盘', content: '具体复盘内容', project_id: 'p1',
    })));
  });

  it('clears the project selection after linking a material', async () => {
    listProjects.mockResolvedValue({
      items: [
        { id: 'p1', title: '一次真实调整', status: 'preparing' },
        { id: 'p2', title: '第二个项目', status: 'preparing' },
      ],
      total: 2,
    });
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    await screen.findByText('失败现场');

    fireEvent.mouseDown(screen.getByLabelText('复用到项目'));
    fireEvent.click(screen.getByRole('option', { name: '第二个项目' }));
    fireEvent.click(screen.getByRole('button', { name: '关联' }));

    await waitFor(() => expect(addMaterialUsage).toHaveBeenCalledWith(
      'm1',
      expect.objectContaining({ project_id: 'p2' }),
    ));
    // Audit e54a2643 medium: 关联成功后选中值必须清空，
    // 否则刷新后选项掉出列表，MUI select 回显失同步。
    await waitFor(() => expect(screen.getByRole('button', { name: '关联' })).toBeDisabled());
  });

  it('clears the previous error as soon as a new operation starts', async () => {
    listProjects.mockResolvedValue({
      items: [
        { id: 'p1', title: '一次真实调整', status: 'preparing' },
        { id: 'p2', title: '第二个项目', status: 'preparing' },
      ],
      total: 2,
    });
    createMaterial.mockRejectedValueOnce(new Error('保存失败原因'));
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    await screen.findByText('失败现场');

    fireEvent.click(screen.getByRole('button', { name: '添加素材' }));
    fireEvent.change(screen.getByLabelText(/素材标题/), { target: { value: '方法复盘' } });
    fireEvent.change(screen.getByLabelText(/素材内容/), { target: { value: '具体复盘内容' } });
    fireEvent.click(screen.getByRole('button', { name: '保存素材' }));
    await screen.findByText('保存失败原因');

    let release!: () => void;
    addMaterialUsage.mockImplementation(() => new Promise((resolve) => {
      release = () => resolve({ id: 'u2' });
    }));
    fireEvent.mouseDown(screen.getByLabelText('复用到项目'));
    fireEvent.click(screen.getByRole('option', { name: '第二个项目' }));
    fireEvent.click(screen.getByRole('button', { name: '关联' }));

    // Audit e54a2643 medium: 新操作开始时就要清掉旧错误，
    // 而不是等旧请求的 load() 收尾。
    await waitFor(() => expect(screen.queryByText('保存失败原因')).not.toBeInTheDocument());
    release();
    await waitFor(() => expect(addMaterialUsage).toHaveBeenCalled());
  });

  it('shows a safe size when material size is missing', async () => {
    listMaterials.mockResolvedValue({
      items: [{
        id: 'm1', title: '失败现场', kind: 'text', mime_type: 'text/plain',
        content: '一次真实失败', privacy_level: 'private', version: 1,
        usages: [], created_at: '2026-08-06T00:00:00Z', updated_at: '2026-08-06T00:00:00Z',
      }],
      total: 1,
    });
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);

    // Audit e54a2643 medium: 后端缺 size 时 undefined/1024 渲染成 NaN KB。
    expect(await screen.findByText(/文字 · 1 KB/)).toBeInTheDocument();
  });

  it('rejects an empty file upload instead of posting empty base64', async () => {
    render(<MemoryRouter><MaterialsPage /></MemoryRouter>);
    await screen.findByText('失败现场');

    fireEvent.click(screen.getByRole('button', { name: '添加素材' }));
    fireEvent.mouseDown(screen.getByLabelText('素材类型'));
    fireEvent.click(screen.getByRole('option', { name: '图片' }));
    fireEvent.change(screen.getByLabelText(/素材标题/), { target: { value: '空图' } });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File([], 'empty.png', { type: 'image/png' })] } });
    fireEvent.click(screen.getByRole('button', { name: '保存素材' }));

    // Audit e54a2643 medium: 空文件会读出空 base64，不应直接提交。
    expect(await screen.findByText('文件内容为空')).toBeInTheDocument();
    expect(createMaterial).not.toHaveBeenCalled();
  });
});
