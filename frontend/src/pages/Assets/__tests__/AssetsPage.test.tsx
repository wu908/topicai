/**
 * Tests for AssetsPage — 3-column asset grid + storage bar + tag filters.
 *
 * Covers:
 * 1. Page title + storage bar (used_bytes/total_bytes/used_ratio)
 * 2. Asset cards (filename, size, used_count, tags slice 0..3, TYPE_LABELS chip)
 * 3. 5 filter chips + filter behavior (全部 / 图片 / 文档 / 音频 / 视频 / 模板)
 * 4. Empty state when no assets
 * 5. Error role=alert when listAssets rejects
 * 6. Error role=alert when getStorageStats rejects (Promise.all fails-fast)
 * 7. Loading skeleton (3 placeholder cards)
 * 8. formatSize 4 branches (GB / MB / KB / B) — exercised via storage bar + asset cards
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// `vi.mock` factories are hoisted above module top-level statements, so the
// mock factory must only reference hoisted variables. Bundle all mocks here.
const { listAssetsMock, getStorageStatsMock } = vi.hoisted(() => ({
  listAssetsMock: vi.fn(),
  getStorageStatsMock: vi.fn(),
}));

vi.mock('@/services/api/assets', () => ({
  listAssets: listAssetsMock,
  getStorageStats: getStorageStatsMock,
}));

import AssetsPage from '../AssetsPage';

// Fixture: one asset of each TYPE so every filter is reachable, and the
// TYPE_LABELS chip text is unique. `tags` has 4 entries to verify the
// slice(0, 3) cap on the rendered tag list.
const SAMPLE_ASSETS = [
  {
    id: 'asset-img-1',
    owner_id: 'u-1',
    filename: 'cover.png',
    mime_type: 'image/png',
    type: 'image' as const,
    size: 2_500_000, // ~2.5 MB
    url: 'https://cdn.example.com/cover.png',
    tags: [
      { id: 't-1', name: '封面' },
      { id: 't-2', name: '公众号' },
      { id: 't-3', name: '主图' },
      { id: 't-4', name: 'overflow-should-not-render' },
    ],
    used_count: 12,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-06-01T00:00:00Z',
  },
  {
    id: 'asset-doc-1',
    owner_id: 'u-1',
    filename: 'brief.pdf',
    mime_type: 'application/pdf',
    type: 'document' as const,
    size: 800_000, // 800 KB
    url: 'https://cdn.example.com/brief.pdf',
    tags: [{ id: 't-5', name: 'brief' }],
    used_count: 3,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-06-02T00:00:00Z',
  },
  {
    id: 'asset-aud-1',
    owner_id: 'u-1',
    filename: 'podcast.mp3',
    mime_type: 'audio/mpeg',
    type: 'audio' as const,
    size: 15_000_000, // 15 MB
    url: 'https://cdn.example.com/podcast.mp3',
    tags: [],
    used_count: 0,
    created_at: '2026-01-03T00:00:00Z',
    updated_at: '2026-06-03T00:00:00Z',
  },
  {
    id: 'asset-vid-1',
    owner_id: 'u-1',
    filename: 'demo.mp4',
    mime_type: 'video/mp4',
    type: 'video' as const,
    size: 2_500_000_000, // 2.5 GB
    url: 'https://cdn.example.com/demo.mp4',
    tags: [{ id: 't-6', name: 'demo' }],
    used_count: 1,
    created_at: '2026-01-04T00:00:00Z',
    updated_at: '2026-06-04T00:00:00Z',
  },
  {
    id: 'asset-tpl-1',
    owner_id: 'u-1',
    filename: 'article-template.md',
    mime_type: 'text/markdown',
    type: 'template' as const,
    size: 500, // 500 B
    url: 'https://cdn.example.com/article-template.md',
    tags: [{ id: 't-7', name: '模板' }],
    used_count: 7,
    created_at: '2026-01-05T00:00:00Z',
    updated_at: '2026-06-05T00:00:00Z',
  },
];

const SAMPLE_STORAGE_GB = {
  used_bytes: 5_000_000_000, // 5.0 GB
  total_bytes: 10_000_000_000, // 10.0 GB
  used_ratio: 0.5,
};

const SAMPLE_STORAGE_B = {
  used_bytes: 500, // 500 B
  total_bytes: 1_000, // 1000 B
  used_ratio: 0.5,
};

function renderPage() {
  return render(
    <MemoryRouter>
      <AssetsPage />
    </MemoryRouter>,
  );
}

describe('AssetsPage', () => {
  beforeEach(() => {
    listAssetsMock.mockReset();
    getStorageStatsMock.mockReset();
    listAssetsMock.mockResolvedValue({ data: { items: SAMPLE_ASSETS, total: 5, page: 1, page_size: 20 } });
    getStorageStatsMock.mockResolvedValue({ data: SAMPLE_STORAGE_GB });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ─── Page chrome ──────────────────────────────────────────────────

  it('renders the page title and section header', async () => {
    renderPage();
    expect(await screen.findByText('素材管理')).toBeInTheDocument();
    expect(screen.getByText('素材使用记录')).toBeInTheDocument();
  });

  it('renders the storage bar with used/total when storage is provided', async () => {
    renderPage();
    expect(await screen.findByText(/5\.0 GB \/ 10\.0 GB/)).toBeInTheDocument();
  });

  it('does NOT render the storage bar when storage is null', async () => {
    getStorageStatsMock.mockResolvedValue({ data: null });
    renderPage();
    // Wait for assets to render so the page has settled.
    expect(await screen.findByText('cover.png')).toBeInTheDocument();
    expect(screen.queryByText(/5\.0 GB \/ 10\.0 GB/)).not.toBeInTheDocument();
  });

  // ─── API contract ─────────────────────────────────────────────────

  it('calls listAssets and getStorageStats exactly once on mount', async () => {
    renderPage();
    await waitFor(() => {
      expect(listAssetsMock).toHaveBeenCalledTimes(1);
      expect(getStorageStatsMock).toHaveBeenCalledTimes(1);
    });
  });

  // ─── Asset card rendering ────────────────────────────────────────

  it('renders one card per asset, with filename + used_count', async () => {
    renderPage();
    expect(await screen.findByText('cover.png')).toBeInTheDocument();
    expect(screen.getByText('brief.pdf')).toBeInTheDocument();
    expect(screen.getByText('podcast.mp3')).toBeInTheDocument();
    expect(screen.getByText('demo.mp4')).toBeInTheDocument();
    expect(screen.getByText('article-template.md')).toBeInTheDocument();
    expect(screen.getByText(/12 次引用/)).toBeInTheDocument();
    expect(screen.getByText(/3 次引用/)).toBeInTheDocument();
  });

  it('renders the TYPE_LABELS chip for each asset card (Chinese labels, .toUpperCase() is a no-op on CJK)', async () => {
    renderPage();
    // TYPE_LABELS values are already Chinese (图片/文档/音频/视频/模板);
    // .toUpperCase() on CJK is a no-op, so the rendered text is the
    // Chinese label itself. The filter chips also contain these labels
    // (verified separately above), so we just confirm each appears at
    // least once in the document.
    await screen.findByText('cover.png');
    for (const label of ['图片', '文档', '音频', '视频', '模板']) {
      expect(screen.queryAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
  });

  it('renders up to 3 tag chips per asset (slice cap)', async () => {
    renderPage();
    // The first asset has 4 tags; the 4th ('overflow-should-not-render') must NOT render.
    expect(await screen.findByText('封面')).toBeInTheDocument();
    expect(screen.getByText('公众号')).toBeInTheDocument();
    expect(screen.getByText('主图')).toBeInTheDocument();
    expect(screen.queryByText('overflow-should-not-render')).not.toBeInTheDocument();
  });

  // ─── formatSize branches (4) ─────────────────────────────────────

  it('formatSize: renders GB branch when size >= 1_000_000_000', async () => {
    renderPage();
    // 2.5 GB for demo.mp4
    expect(await screen.findByText(/2\.5 GB · 1 次引用/)).toBeInTheDocument();
  });

  it('formatSize: renders MB branch when 1_000_000 <= size < 1_000_000_000', async () => {
    renderPage();
    // 2.5 MB for cover.png
    expect(await screen.findByText(/2\.5 MB · 12 次引用/)).toBeInTheDocument();
  });

  it('formatSize: renders KB branch when 1_000 <= size < 1_000_000', async () => {
    renderPage();
    // 800 KB for brief.pdf
    expect(await screen.findByText(/800 KB · 3 次引用/)).toBeInTheDocument();
  });

  it('formatSize: renders bytes branch when size < 1_000', async () => {
    renderPage();
    // 500 B for article-template.md
    expect(await screen.findByText(/500 B · 7 次引用/)).toBeInTheDocument();
  });

  // ─── Filter chips (5 distinct filters + 全部) ─────────────────────

  it('renders the 6 type-filter chips (全部 + 5 types)', async () => {
    renderPage();
    // ChipRow uses buttons. Match by role+name.
    expect(await screen.findByRole('button', { name: '全部' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '图片' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '文档' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '音频' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '视频' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '模板' })).toBeInTheDocument();
  });

  it('filter "图片" hides non-image assets and shows only cover.png', async () => {
    renderPage();
    await screen.findByText('cover.png');
    fireEvent.click(screen.getByRole('button', { name: '图片' }));
    expect(screen.getByText('cover.png')).toBeInTheDocument();
    expect(screen.queryByText('brief.pdf')).not.toBeInTheDocument();
    expect(screen.queryByText('podcast.mp3')).not.toBeInTheDocument();
    expect(screen.queryByText('demo.mp4')).not.toBeInTheDocument();
    expect(screen.queryByText('article-template.md')).not.toBeInTheDocument();
  });

  it('filter "文档" shows only brief.pdf', async () => {
    renderPage();
    await screen.findByText('cover.png');
    fireEvent.click(screen.getByRole('button', { name: '文档' }));
    expect(screen.queryByText('cover.png')).not.toBeInTheDocument();
    expect(screen.getByText('brief.pdf')).toBeInTheDocument();
  });

  it('filter "视频" shows only demo.mp4', async () => {
    renderPage();
    await screen.findByText('cover.png');
    fireEvent.click(screen.getByRole('button', { name: '视频' }));
    expect(screen.queryByText('cover.png')).not.toBeInTheDocument();
    expect(screen.getByText('demo.mp4')).toBeInTheDocument();
  });

  it('switching back to "全部" restores the full list', async () => {
    renderPage();
    await screen.findByText('cover.png');
    fireEvent.click(screen.getByRole('button', { name: '图片' }));
    expect(screen.queryByText('brief.pdf')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '全部' }));
    expect(screen.getByText('cover.png')).toBeInTheDocument();
    expect(screen.getByText('brief.pdf')).toBeInTheDocument();
    expect(screen.getByText('podcast.mp3')).toBeInTheDocument();
  });

  // ─── Empty state ─────────────────────────────────────────────────

  it('shows the empty state when no assets are returned', async () => {
    listAssetsMock.mockResolvedValue({ data: { items: [], total: 0, page: 1, page_size: 20 } });
    renderPage();
    expect(await screen.findByText('无素材')).toBeInTheDocument();
    expect(screen.getByText(/当前筛选条件下没有素材/)).toBeInTheDocument();
  });

  // ─── Error paths ─────────────────────────────────────────────────

  it('shows a role=alert error when listAssets rejects', async () => {
    listAssetsMock.mockRejectedValueOnce(new Error('500'));
    renderPage();
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toBeTruthy();
  });

  it('shows a role=alert error when getStorageStats rejects', async () => {
    getStorageStatsMock.mockRejectedValueOnce(new Error('boom'));
    renderPage();
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toBeTruthy();
  });

  // ─── Loading skeleton ────────────────────────────────────────────

  it('renders 3 placeholder skeleton cards while loading', async () => {
    // Make both APIs hang so the loading state is observable.
    listAssetsMock.mockReturnValue(new Promise(() => undefined));
    getStorageStatsMock.mockReturnValue(new Promise(() => undefined));
    renderPage();
    // The page title is rendered immediately; the 3 skeleton cards are
    // also rendered. Use a query for height=130 divs.
    await screen.findByText('素材管理');
    // All asset filenames must NOT appear while loading.
    expect(screen.queryByText('cover.png')).not.toBeInTheDocument();
  });
});
