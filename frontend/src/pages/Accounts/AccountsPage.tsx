/**
 * Accounts page — V3 design + Phase 7 backend contract wired.
 * Renders connected-platform cards + add-platform tiles + team member rows.
 * - listAccounts / listTeam: wired in Phase 8 (real API).
 * - changeMemberRole / removeMember: wired in Phase 8 (real API, optimistic
 *   with rollback on error).
 * - createAccount / syncAccount: Phase 9a wired (modals + onClick).
 * - 4 platform tiles + inviteMember: still Phase 9+ placeholders.
 */
import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { extractErrorMessage } from '@/utils/error';
import Modal from '@/components/common/Modal';
import type {
  PlatformAccount,
  TeamMember,
  TeamRole,
  Platform,
} from '@/types/contracts/accounts';
import {
  listAccounts,
  listTeam,
  changeMemberRole,
  removeMember,
  createAccount,
  syncAccount,
  inviteMember,
} from '@/services/api/accounts';

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

// Phase 9a: simple OAuth-style add-account modal.
// In production this would redirect to the platform's OAuth flow; here
// we accept platform + display_name and POST to /accounts, which the
// backend creates in 'disconnected' status (real OAuth handshake is
// a future task).
interface AddAccountModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (account: PlatformAccount) => void;
  prefillPlatform?: Platform;
}

function AddAccountModal({ open, onClose, onCreated, prefillPlatform }: AddAccountModalProps): React.ReactElement {
  const [platform, setPlatform] = useState<Platform>(prefillPlatform ?? 'wechat_mp');
  // When a different platform tile triggers the modal, reset to that platform.
  /* eslint-disable react-hooks/set-state-in-effect -- prefillPlatform prop drives platform state on modal open */
  useEffect(() => {
    if (prefillPlatform) setPlatform(prefillPlatform);
  }, [prefillPlatform, open]);
   

  // AddAccountModal body...
  const [displayName, setDisplayName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Reset form whenever modal opens.
  /* eslint-disable react-hooks/set-state-in-effect -- reset form fields on modal open */
  useEffect(() => {
    if (open) {
      setDisplayName('');
      setLocalError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!displayName.trim()) {
      setLocalError('请输入账号显示名');
      return;
    }
    setSubmitting(true);
    setLocalError(null);
    try {
      const res = await createAccount({ platform, display_name: displayName.trim() });
      if (res.data) onCreated(res.data);
      onClose();
    } catch (err: unknown) {
      setLocalError(extractErrorMessage(err, '创建账号失败'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="添加平台账号"
      footer={
        <>
          <button type="button" onClick={onClose} style={secondaryBtn}>
            取消
          </button>
          <button
            type="submit"
            form="add-account-form"
            disabled={submitting}
            style={primaryBtn}
          >
            {submitting ? '创建中...' : '创建账号'}
          </button>
        </>
      }
    >
      <form id="add-account-form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
          平台
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value as Platform)}
            style={{ height: 36, padding: '0 10px', border: '1px solid var(--v3-border)', borderRadius: 6, background: 'var(--v3-surface)' }}
          >
            <option value="wechat_mp">微信公众号</option>
            <option value="wechat_video">视频号</option>
            <option value="xhs">小红书</option>
            <option value="bilibili">B 站</option>
            <option value="douyin">抖音</option>
            <option value="zhihu">知乎</option>
          </select>
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
          账号显示名
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="例如：我的公众号"
            style={{ height: 36, padding: '0 10px', border: '1px solid var(--v3-border)', borderRadius: 6, background: 'var(--v3-surface)' }}
          />
        </label>
        {localError && (
          <div role="alert" style={{ fontSize: 12, color: 'var(--v3-red)' }}>{localError}</div>
        )}
      </form>
    </Modal>
  );
}

// Phase 9b: invite member modal. Sends an email + role to the backend
// /team/members endpoint. Real email delivery is a future task; for now
// the backend records the invite in its own DB and returns the new member.
interface InviteMemberModalProps {
  open: boolean;
  onClose: () => void;
  onInvited: (member: TeamMember) => void;
}

function InviteMemberModal({ open, onClose, onInvited }: InviteMemberModalProps): React.ReactElement {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [role, setRole] = useState<TeamRole>('editor');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  /* eslint-disable react-hooks/set-state-in-effect -- reset invite form on modal open */
  useEffect(() => {
    if (open) {
      setEmail('');
      setUsername('');
      setRole('editor');
      setLocalError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!email.trim() || !username.trim()) {
      setLocalError('请输入邮箱和用户名');
      return;
    }
    setSubmitting(true);
    setLocalError(null);
    try {
      const res = await inviteMember({
        email: email.trim(),
        username: username.trim(),
        role,
      });
      if (res.data) onInvited(res.data);
      onClose();
    } catch (err: unknown) {
      setLocalError(extractErrorMessage(err, '邀请失败'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="邀请团队成员"
      footer={
        <>
          <button type="button" onClick={onClose} style={secondaryBtn}>取消</button>
          <button type="submit" form="invite-form" disabled={submitting} style={primaryBtn}>
            {submitting ? '发送中...' : '发送邀请'}
          </button>
        </>
      }
    >
      <form id="invite-form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
          邮箱
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="member@example.com"
            style={{ height: 36, padding: '0 10px', border: '1px solid var(--v3-border)', borderRadius: 6, background: 'var(--v3-surface)' }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
          用户名
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="显示名称"
            style={{ height: 36, padding: '0 10px', border: '1px solid var(--v3-border)', borderRadius: 6, background: 'var(--v3-surface)' }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
          角色
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as TeamRole)}
            style={{ height: 36, padding: '0 10px', border: '1px solid var(--v3-border)', borderRadius: 6, background: 'var(--v3-surface)' }}
          >
            {(['admin', 'editor', 'viewer'] as TeamRole[]).map((r) => (
              <option key={r} value={r}>{ROLE_LABELS[r]}</option>
            ))}
          </select>
        </label>
        {localError && (
          <div role="alert" style={{ fontSize: 12, color: 'var(--v3-red)' }}>{localError}</div>
        )}
      </form>
    </Modal>
  );
}

const AccountsPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingRoleChange, setPendingRoleChange] = useState<string | null>(null);
  const [pendingRemove, setPendingRemove] = useState<string | null>(null);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [prefillPlatform, setPrefillPlatform] = useState<Platform>('wechat_mp');
  const [pendingSync, setPendingSync] = useState(false);
  const [showInvite, setShowInvite] = useState(false);

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

  const handleRoleChange = async (memberId: string, newRole: TeamRole): Promise<void> => {
    // Optimistic update — flip the role locally, call the API, roll back on
    // failure. The backend's "last admin cannot be demoted" rule returns
    // 422, which we surface as an inline error rather than silently failing.
    const previous = team.find((m) => m.id === memberId)?.role;
    if (previous === newRole) return;
    setPendingRoleChange(memberId);
    setTeam((prev) =>
      prev.map((m) => (m.id === memberId ? { ...m, role: newRole } : m)),
    );
    try {
      await changeMemberRole(memberId, { role: newRole });
    } catch (err: unknown) {
      // Roll back to the previous role on any error.
      if (previous) {
        setTeam((prev) =>
          prev.map((m) => (m.id === memberId ? { ...m, role: previous } : m)),
        );
      }
      setError(extractErrorMessage(err, '角色更新失败'));
    } finally {
      setPendingRoleChange(null);
    }
  };

  const handleRemove = async (memberId: string): Promise<void> => {
    // Optimistic remove — hide the row immediately, call the API, restore
    // on failure. Backend returns 422 if the member is the last admin.
    const removed = team.find((m) => m.id === memberId);
    if (!removed) return;
    setPendingRemove(memberId);
    setTeam((prev) => prev.filter((m) => m.id !== memberId));
    try {
      await removeMember(memberId);
    } catch (err: unknown) {
      // Restore the removed member at its original position.
      setTeam((prev) => {
        if (prev.some((m) => m.id === memberId)) return prev;
        return [...prev, removed].sort((a, b) => a.id.localeCompare(b.id));
      });
      setError(extractErrorMessage(err, '成员移除失败'));
    } finally {
      setPendingRemove(null);
    }
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
          onClick={() => setShowAddAccount(true)}
        >
          + 添加账号
        </button>
        <button
          type="button"
          style={secondaryBtn}
          disabled={pendingSync}
          onClick={async () => {
            if (accounts.length === 0) {
              setError('请先添加账号');
              return;
            }
            setPendingSync(true);
            try {
              const target = accounts.find((a) => a.status === 'connected') ?? accounts[0];
              await syncAccount(target.id);
              // Refresh to get fresh last_sync_at.
              const res = await listAccounts();
              setAccounts(res.data || []);
            } catch (err: unknown) {
              setError(extractErrorMessage(err, '同步失败'));
            } finally {
              setPendingSync(false);
            }
          }}
        >
          {pendingSync ? '同步中...' : '同步数据'}
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
              onClick={() => {
                setPrefillPlatform(p);
                setShowAddAccount(true);
              }}
              style={{
                background: 'var(--v3-surface)',
                border: '1px solid var(--v3-border)',
                borderRadius: 8,
                padding: '12px 8px',
                textAlign: 'center',
                cursor: 'pointer',
                fontFamily: 'inherit',
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
          onClick={() => setShowInvite(true)}
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

      <AddAccountModal
        open={showAddAccount}
        onClose={() => setShowAddAccount(false)}
        onCreated={(acc) => setAccounts((prev) => [acc, ...prev])}
        prefillPlatform={prefillPlatform}
      />

      <InviteMemberModal
        open={showInvite}
        onClose={() => setShowInvite(false)}
        onInvited={(m) => setTeam((prev) => [...prev, m])}
      />
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
