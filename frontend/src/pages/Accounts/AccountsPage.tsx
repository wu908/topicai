/**
 * Accounts page — V3 design + Phase 7 backend contract wired.
 * Renders connected-platform cards + add-platform tiles + team member rows.
 * Data is hard-coded mock typed against @/types/contracts/accounts.
 * Replace mock arrays with API calls when backend implements
 * /accounts + /team/members.
 */
import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { extractErrorMessage } from '@/utils/error';
import type {
  PlatformAccount,
  TeamMember,
  TeamRole,
} from '@/types/contracts/accounts';
import { listAccounts, listTeam } from '@/services/api/accounts';

const PLATFORM_LABELS: Record<PlatformAccount['platform'], string> = {
  wechat_mp: '微信公众号',
  wechat_video: '视频号',
  xhs: '小红书',
  bilibili: 'B 站',
  douyin: '抖音',
  zhihu: '知乎',
};

const PLATFORM_AVATARS: Record<PlatformAccount['platform'], string> = {
  wechat_mp: '公',
  wechat_video: '视',
  xhs: '小',
  bilibili: 'B',
  douyin: '抖',
  zhihu: '知',
};

const AVAILABLE_PLATFORMS: Array<PlatformAccount['platform']> = [
  'wechat_video',
  'bilibili',
  'douyin',
  'zhihu',
];

const ROLE_LABELS: Record<TeamRole, string> = {
  admin: '管理员',
  editor: '编辑',
  viewer: '查看者',
};

function formatNumber(n: number): string {
  if (n >= 10_000) return `${(n / 10_000).toFixed(1)}W`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

const AccountsPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingRoleChange, setPendingRoleChange] = useState<string | null>(null);
  const [pendingRemove, setPendingRemove] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async (): Promise<void> => {
      try {
        const [accsRes, teamRes] = await Promise.all([
          listAccounts(),
          listTeam(),
        ]);
        if (cancelled) return;
        setAccounts(accsRes.data || []);
        setTeam(teamRes.data || []);
        setLoading(false);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(extractErrorMessage(err, '账号加载失败'));
          setLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleRoleChange = (memberId: string, newRole: TeamRole): void => {
    // Backend replacement: PATCH /api/v1/team/members/{id} { role: newRole }
    setPendingRoleChange(memberId);
    setTeam((prev) =>
      prev.map((m) => (m.id === memberId ? { ...m, role: newRole } : m)),
    );
    window.setTimeout(() => setPendingRoleChange(null), 800);
  };

  const handleRemove = (memberId: string): void => {
    // Backend replacement: DELETE /api/v1/team/members/{id}
    setPendingRemove(memberId);
    setTeam((prev) => prev.filter((m) => m.id !== memberId));
    window.setTimeout(() => setPendingRemove(null), 800);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 600,
            letterSpacing: '-0.3px',
            color: 'var(--v3-text)',
            margin: 0,
          }}
        >
          账号管理
        </h1>
        <p
          style={{
            fontSize: 13,
            color: 'var(--v3-text-sec)',
            marginTop: 4,
            lineHeight: 1.5,
          }}
        >
          管理你的公众号、视频号、小红书等创作平台账号。
        </p>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            fontSize: 12.5,
            color: 'var(--v3-red)',
            padding: 12,
            border: '1px solid rgba(196,69,61,0.2)',
            borderRadius: 6,
            background: 'var(--v3-surface)',
          }}
        >
          {error}
        </div>
      )}

      {/* Header actions */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button
          type="button"
          style={primaryBtn}
        >
          + 添加账号
        </button>
        <button type="button" style={secondaryBtn}>
          同步数据
        </button>
      </div>

      {/* Connected accounts */}
      <section>
        <h2 style={sectionTitle}>已连接账号</h2>
        {loading ? (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 12,
            }}
          >
            {[1, 2].map((i) => (
              <div
                key={i}
                style={{
                  background: 'var(--v3-surface)',
                  border: '1px solid var(--v3-border)',
                  borderRadius: 8,
                  height: 90,
                }}
              />
            ))}
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 12,
            }}
          >
            {accounts.map((a) => (
              <div key={a.id} style={accountCardStyle}>
                <div
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: '50%',
                    background: 'var(--v3-panel-bg)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--v3-text-sec)',
                    flexShrink: 0,
                  }}
                >
                  {PLATFORM_AVATARS[a.platform]}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      flexWrap: 'wrap',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 14,
                        fontWeight: 500,
                        color: 'var(--v3-text)',
                      }}
                    >
                      {a.display_name}
                    </span>
                    {a.is_primary && (
                      <span style={primaryTagStyle}>主账号</span>
                    )}
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: 'var(--v3-text-sec)',
                      marginTop: 1,
                    }}
                  >
                    {PLATFORM_LABELS[a.platform]}
                  </div>
                  {a.stats && (
                    <div
                      style={{
                        fontSize: 12,
                        color: 'var(--v3-text-sec)',
                        marginTop: 4,
                        display: 'flex',
                        gap: 12,
                      }}
                    >
                      <span>粉丝 <strong style={{ color: 'var(--v3-text)' }}>{formatNumber(a.stats.followers)}</strong></span>
                      <span>文章 <strong style={{ color: 'var(--v3-text)' }}>{a.stats.articles}</strong></span>
                      <span>平均阅读 <strong style={{ color: 'var(--v3-text)' }}>{formatNumber(a.stats.avg_read_count)}</strong></span>
                    </div>
                  )}
                </div>
                <div
                  style={{
                    fontSize: 11.5,
                    color: a.status === 'connected' ? 'var(--v3-green)' : 'var(--v3-amber)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    flexShrink: 0,
                  }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: a.status === 'connected' ? 'var(--v3-green)' : 'var(--v3-amber)',
                    }}
                  />
                  {a.status === 'connected' ? '已连接' : '需要重新授权'}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Add new platform */}
      <section>
        <h2 style={sectionTitle}>添加新平台</h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 10,
          }}
        >
          {AVAILABLE_PLATFORMS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => undefined}
              style={{
                background: 'var(--v3-surface)',
                border: '1px solid var(--v3-border)',
                borderRadius: 8,
                padding: '12px 8px',
                textAlign: 'center',
                cursor: 'pointer',
                fontFamily: 'inherit',
                transition: 'border-color 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--v3-text)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--v3-border)';
              }}
            >
              <div
                style={{
                  fontSize: 13.5,
                  fontWeight: 500,
                  color: 'var(--v3-text)',
                }}
              >
                {PLATFORM_LABELS[p]}
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: 'var(--v3-text-sec)',
                  marginTop: 2,
                }}
              >
                点击连接
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Team members */}
      <section>
        <h2 style={sectionTitle}>团队成员</h2>
        {team.map((m) => (
          <div
            key={m.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 0',
              borderBottom: '1px solid var(--v3-border-light)',
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: 'var(--v3-panel-bg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 12,
                fontWeight: 600,
                color: 'var(--v3-text-sec)',
                flexShrink: 0,
              }}
            >
              {m.initial}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 500, color: 'var(--v3-text)' }}>
                {m.username}
              </div>
              <div style={{ fontSize: 12, color: 'var(--v3-text-sec)' }}>{m.email}</div>
            </div>
            <select
              value={m.role}
              onChange={(e) => handleRoleChange(m.id, e.target.value as TeamRole)}
              disabled={pendingRoleChange === m.id}
              aria-label={`${m.username} 角色`}
              style={{
                height: 32,
                padding: '0 8px',
                border: '1px solid var(--v3-border)',
                borderRadius: 6,
                background: 'var(--v3-surface)',
                color: 'var(--v3-text)',
                fontSize: 13,
                fontFamily: 'inherit',
                cursor: 'pointer',
              }}
            >
              {(['admin', 'editor', 'viewer'] as TeamRole[]).map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
            {m.role !== 'admin' && (
              <button
                type="button"
                onClick={() => handleRemove(m.id)}
                disabled={pendingRemove === m.id}
                style={{
                  height: 32,
                  padding: '0 8px',
                  marginLeft: 4,
                  border: '1px solid var(--v3-red-border)',
                  background: 'var(--v3-surface)',
                  color: 'var(--v3-red)',
                  borderRadius: 6,
                  fontSize: 12,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                {pendingRemove === m.id ? '移除中...' : '移除'}
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={() => undefined}
          style={{
            ...primaryBtn,
            marginTop: 12,
          }}
        >
          + 邀请成员
        </button>
      </section>

      {/* Account overview aside */}
      <div
        style={{
          background: 'var(--v3-panel-bg)',
          borderRadius: 8,
          padding: '16px 18px',
          display: 'flex',
          gap: 24,
          fontSize: 13,
          color: 'var(--v3-text-sec)',
        }}
      >
        <div>
          <div style={{ fontWeight: 500, color: 'var(--v3-text)' }}>账号总览</div>
          <div style={{ marginTop: 4, fontSize: 12 }}>3 个已连接账号 · 总粉丝 37.3K</div>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 12 }}>当前账号：{user?.username ?? '—'}</div>
      </div>
    </div>
  );
};

const primaryBtn: React.CSSProperties = {
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
};

const secondaryBtn: React.CSSProperties = {
  height: 36,
  padding: '0 16px',
  borderRadius: 6,
  background: 'var(--v3-surface)',
  color: 'var(--v3-text)',
  border: '1px solid var(--v3-border)',
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
  fontFamily: 'inherit',
};

const sectionTitle: React.CSSProperties = {
  fontSize: 15,
  fontWeight: 600,
  marginTop: 12,
  marginBottom: 12,
  color: 'var(--v3-text)',
};

const accountCardStyle: React.CSSProperties = {
  background: 'var(--v3-surface)',
  border: '1px solid var(--v3-border)',
  borderRadius: 8,
  padding: 18,
  display: 'flex',
  alignItems: 'center',
  gap: 14,
  boxShadow: 'var(--v3-shadow-card)',
};

const primaryTagStyle: React.CSSProperties = {
  fontSize: 11,
  padding: '1px 6px',
  marginLeft: 6,
  background: 'var(--v3-text)',
  color: '#fff',
  borderRadius: 3,
  fontWeight: 500,
};

export default AccountsPage;
