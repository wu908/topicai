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
});
