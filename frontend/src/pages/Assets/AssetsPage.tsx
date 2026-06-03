/**
 * Assets page — V3 design + Phase 7 backend contract wired.
 * Renders a 3-column asset grid + storage bar + tag filters.
 * Data is a hard-coded mock list typed against the contracts in
 * @/types/contracts/assets. When the backend implements the real
 * endpoints, only `loadAssets()` / `loadStorage()` need to swap to API
 * calls — the types already enforce the shape.
 */
import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import ChipRow from '@/components/common/ChipRow';
import EmptyState from '@/components/common/EmptyState';
import { extractErrorMessage } from '@/utils/error';
import type { Asset, AssetType, AssetStorageStats } from '@/types/contracts/assets';
import { listAssets, getStorageStats } from '@/services/api/assets';

const TYPE_LABELS: Record<AssetType, string> = {
  image: '图片',
  document: '文档',
  audio: '音频',
  video: '视频',
  template: '模板',
};

const TYPE_FILTERS = ['全部', '图片', '文档', '音频', '视频', '模板'] as const;

// ─── Hard-coded mock data (replace with API calls when backend ready) ─
function formatSize(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(0)} KB`;
  return `${bytes} B`;
}

const AssetsPage: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [storage, setStorage] = useState<AssetStorageStats | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('全部');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async (): Promise<void> => {
      try {
        const [assetsRes, storageRes] = await Promise.all([
          listAssets(),
          getStorageStats(),
        ]);
        if (cancelled) return;
        setAssets(assetsRes.data?.items || []);
        setStorage(storageRes.data || null);
        setLoading(false);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(extractErrorMessage(err, '素材加载失败'));
          setLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredAssets =
    activeFilter === '全部'
      ? assets
      : assets.filter((a) => TYPE_LABELS[a.type] === activeFilter);

  return (
    <PageContainer
      title="素材管理"
      subtitle="统一管理你的图片、文档、音频等创作素材。"
    >
      {/* Storage bar */}
      {storage && (
        <div
          style={{
            background: 'var(--v3-surface)',
            border: '1px solid var(--v3-border)',
            borderRadius: 8,
            padding: '12px 16px',
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            fontSize: 12.5,
            color: 'var(--v3-text-sec)',
          }}
        >
          <span style={{ fontWeight: 500, color: 'var(--v3-text)' }}>
            存储：{formatSize(storage.used_bytes)} / {formatSize(storage.total_bytes)}
          </span>
          <div
            style={{
              flex: 1,
              height: 6,
              background: 'var(--v3-border)',
              borderRadius: 3,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${storage.used_ratio * 100}%`,
                height: '100%',
                background: 'var(--v3-text)',
                borderRadius: 3,
                transition: 'width 0.4s',
              }}
            />
          </div>
        </div>
      )}

      {/* Search + filters + upload */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 20,
          flexWrap: 'wrap',
        }}
      >
        <input
          type="text"
          placeholder="搜索素材…"
          style={{
            flex: 1,
            minWidth: 180,
            height: 36,
            padding: '0 12px',
            border: '1px solid var(--v3-border)',
            borderRadius: 6,
            background: 'var(--v3-bg)',
            color: 'var(--v3-text)',
            fontSize: 13,
            fontFamily: 'inherit',
            outline: 'none',
          }}
        />
        <button
          type="button"
          style={{
            height: 36,
            padding: '0 16px',
            borderRadius: 6,
            background: 'var(--v3-text)',
            color: '#fff',
            border: 'none',
            fontSize: 13,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          上传素材
        </button>
      </div>

      <ChipRow
        options={TYPE_FILTERS as unknown as readonly string[]}
        active={activeFilter}
        onChange={setActiveFilter}
        ariaLabel="素材类型筛选"
      />

      {error && (
        <div
          role="alert"
          style={{
            fontSize: 12.5,
            color: 'var(--v3-red)',
            marginBottom: 16,
            padding: 12,
            border: '1px solid rgba(196,69,61,0.2)',
            borderRadius: 6,
          }}
        >
          {error}
        </div>
      )}

      {loading ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 12,
          }}
        >
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                background: 'var(--v3-surface)',
                border: '1px solid var(--v3-border)',
                borderRadius: 8,
                overflow: 'hidden',
                height: 130,
              }}
            />
          ))}
        </div>
      ) : filteredAssets.length === 0 ? (
        <EmptyState
          title="无素材"
          description="当前筛选条件下没有素材。试试切换类型或上传新素材。"
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 12,
          }}
        >
          {filteredAssets.map((a) => (
            <div
              key={a.id}
              style={{
                background: 'var(--v3-surface)',
                border: '1px solid var(--v3-border)',
                borderRadius: 8,
                overflow: 'hidden',
                boxShadow: 'var(--v3-shadow-card)',
                cursor: 'pointer',
                transition: 'box-shadow 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = 'var(--v3-shadow-card-hover)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'var(--v3-shadow-card)';
              }}
            >
              <div
                style={{
                  width: '100%',
                  height: 90,
                  background: 'var(--v3-panel-bg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--v3-text-ter)',
                  fontSize: 11,
                }}
              >
                {TYPE_LABELS[a.type].toUpperCase()}
              </div>
              <div style={{ padding: '10px 12px' }}>
                <div
                  style={{
                    fontSize: 12.5,
                    fontWeight: 500,
                    color: 'var(--v3-text)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {a.filename}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--v3-text-sec)',
                    marginTop: 2,
                  }}
                >
                  {formatSize(a.size)} · {a.used_count} 次引用
                </div>
                <div
                  style={{
                    display: 'flex',
                    gap: 4,
                    flexWrap: 'wrap',
                    marginTop: 6,
                  }}
                >
                  {a.tags.slice(0, 3).map((t) => (
                    <span
                      key={t.id}
                      style={{
                        padding: '1px 6px',
                        background: 'var(--v3-tag-bg)',
                        color: 'var(--v3-text-sec)',
                        fontSize: 10.5,
                        borderRadius: 3,
                      }}
                    >
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Usage records */}
      <div
        style={{
          fontSize: 15,
          fontWeight: 600,
          marginTop: 28,
          marginBottom: 12,
          color: 'var(--v3-text)',
        }}
      >
        素材使用记录
      </div>
      {([] as any[]).map((u: any) => {
        const a = assets.find((x) => x.id === u.id);
        return (
          <div
            key={u.id}
            style={{
              padding: '12px 0',
              borderBottom: '1px solid var(--v3-border-light)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--v3-text)' }}>
                {a?.filename ?? u.id}
              </div>
              <div style={{ fontSize: 12, color: 'var(--v3-text-sec)', marginTop: 2 }}>
                {u.used_count > 0
                  ? `已用于：「${u.article_title}」`
                  : '未被任何文章引用'}
              </div>
            </div>
            <span
              style={{
                fontSize: 11,
                padding: '1px 6px',
                background: u.used_count > 0 ? 'var(--v3-green-bg)' : 'var(--v3-tag-bg)',
                color: u.used_count > 0 ? 'var(--v3-green)' : 'var(--v3-text-ter)',
                borderRadius: 3,
              }}
            >
              {u.used_count > 0 ? '已引用' : '未使用'}
            </span>
          </div>
        );
      })}
    </PageContainer>
  );
};

export default AssetsPage;
