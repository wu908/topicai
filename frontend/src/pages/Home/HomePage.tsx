/**
 * Home dashboard — V3 design (topicai-v3-login-meta.html).
 * Sections (top-to-bottom):
 *   1. Onboarding banner (dark gradient) — shown until Onboarding done
 *   2. 4-column stats row — 今日阅读 / 新增关注 / 互动率 / 待发布
 *   3. Action row — 发现新选题 / 开始写作 / 查看数据
 *   4. 最近动态 — list of recent activity (with 复盘 link where applicable)
 *   5. AI 建议 — 2 cards with ai-meta + 👍/👎
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useRateLimit } from '@/hooks/useRateLimit';
import PageContainer from '@/components/layout/PageContainer';
import LoadingCard from '@/components/common/LoadingCard';
import { extractErrorMessage } from '@/utils/error';

const RECENT_ACTIVITY = [
  {
    id: 'a1',
    title: '「AI 写作工具横评 2026」发布成功',
    meta: '2 小时前 · 公众号 · 阅读 843 · 点赞 67',
    hasRecap: true,
  },
  {
    id: 'a2',
    title: '「内容团队管理心得」已通过审核，定时 6/3 发布',
    meta: '5 小时前 · 公众号',
    hasRecap: false,
  },
  {
    id: 'a3',
    title: '标题评分系统更新：新增情绪强度维度',
    meta: '1 天前 · 系统通知',
    hasRecap: false,
  },
  {
    id: 'a4',
    title: '「选题方法论 v3」保存为草稿',
    meta: '3 天前 · 草稿箱',
    hasRecap: false,
  },
];

const AI_SUGGESTIONS = [
  {
    id: 's1',
    title: '基于近期热点分析',
    body:
      '「AI 生成内容版权归属」话题热度正在上升，与你账号定位高度相关。建议 24 小时内发布。',
    meta: 'GPT-4o · 置信度 87% · 来源: 微信指数 + 微博热搜',
    link: '/topics',
    linkText: '查看选题 →',
  },
  {
    id: 's2',
    title: '内容优化提醒',
    body: '你上周的「短视频脚本技巧」标题评分仅 6.8，建议重新打磨。',
    meta: 'GPT-4o · 置信度 92% · 来源: 标题评分模型 v2',
    link: '/titles',
    linkText: '去优化 →',
  },
];

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, profile, fetchCurrentUser, fetchProfile } = useAuth();
  const { remaining, usagePercent } = useRateLimit();
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const loadData = async (): Promise<void> => {
      try {
        await Promise.all([fetchCurrentUser(), fetchProfile()]);
        if (!cancelled) setLoading(false);
      } catch (err: unknown) {
        if (!cancelled) {
          setFetchError(extractErrorMessage(err, '数据加载失败，请稍后重试'));
          setLoading(false);
        }
      }
    };
    loadData();
    return () => {
      cancelled = true;
    };
  }, [fetchCurrentUser, fetchProfile]);

  if (loading) {
    return (
      <PageContainer title="首页" subtitle="你的内容运营中心">
        <LoadingCard rows={3} />
        <LoadingCard rows={2} />
      </PageContainer>
    );
  }

  // Onboarding steps: 1=done (account), 2=track, 3=preferences.
  // Use `?.` on both sides to short-circuit when profile is null (e.g.
  // after a failed fetchProfile). Without the inner `?.`, the `.length`
  // access throws on undefined and crashes the page exactly when the
  // new error-handling path wants to show the alert.
  const onboardingDone = !!(profile?.track && profile?.content_formats?.length);

  return (
    <PageContainer
      title={`Good morning, ${user?.username || '创作者'}`}
      subtitle="内容运营中心概览，今日数据已更新。"
    >
      {/* Onboarding banner */}
      {!onboardingDone && (
        <div
          style={{
            background: 'linear-gradient(135deg, #2C2C2C 0%, #3a3a3a 100%)',
            borderRadius: 12,
            padding: '28px 32px',
            marginBottom: 28,
            color: '#fff',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)',
          }}
        >
          <div style={{ fontSize: 20, fontWeight: 600, marginBottom: 6 }}>
            👋 欢迎来到 TopicAI
          </div>
          <div
            style={{
              fontSize: 13,
              color: 'rgba(255,255,255,0.7)',
              marginBottom: 16,
              lineHeight: 1.5,
            }}
          >
            完成初始设置，让 AI 更了解你的内容方向，获得精准的选题与写作建议。
          </div>
          <div style={{ display: 'flex', gap: 20, marginBottom: 18 }}>
            <Step done label="连接账号" />
            <Step label="选择赛道" active={!profile?.track} />
            <Step label="内容偏好" active={!profile?.content_formats?.length} />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              type="button"
              onClick={() => navigate('/profile')}
              style={{
                background: '#fff',
                color: 'var(--v3-text)',
                padding: '8px 16px',
                borderRadius: 6,
                fontSize: 13,
                fontWeight: 500,
                cursor: 'pointer',
                border: '1px solid #fff',
                fontFamily: 'inherit',
              }}
            >
              继续设置 →
            </button>
            <button
              type="button"
              style={{
                background: 'transparent',
                color: '#fff',
                padding: '8px 16px',
                borderRadius: 6,
                fontSize: 13,
                fontWeight: 500,
                cursor: 'pointer',
                border: '1px solid rgba(255,255,255,0.3)',
                fontFamily: 'inherit',
              }}
            >
              稍后提醒
            </button>
          </div>
        </div>
      )}

      {fetchError && (
        <div
          role="alert"
          style={{
            fontSize: 12.5,
            color: 'var(--v3-red)',
            marginBottom: 16,
            padding: 12,
            border: '1px solid rgba(196,69,61,0.2)',
            borderRadius: 6,
            background: 'var(--v3-surface)',
          }}
        >
          {fetchError}
        </div>
      )}

      {/* Stats row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 14,
          marginBottom: 24,
        }}
      >
        <StatCard num="1,247" label="今日阅读" change={{ up: true, text: '↑ 12.3%' }} />
        <StatCard num="38" label="新增关注" change={{ up: true, text: '↑ 5 人' }} />
        <StatCard num="89%" label="互动率" change={{ up: true, text: '高于 7 日均值' }} />
        <StatCard
          num={String(6)}
          label="待发布"
          change={{ up: false, text: '2 篇今日排期' }}
        />
      </div>

      {/* AI quota mini bar (informational, mirrors useRateLimit) */}
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
          AI 今日调用：{remaining} / 20 剩余
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
              width: `${Math.min(100, usagePercent)}%`,
              height: '100%',
              background: usagePercent > 80 ? 'var(--v3-amber)' : 'var(--v3-text)',
              transition: 'width 0.4s',
            }}
          />
        </div>
      </div>

      {/* Action row */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => navigate('/topics')}
          style={actionBtnStyle(true)}
        >
          ✦ 发现新选题
        </button>
        <button
          type="button"
          onClick={() => navigate('/writing')}
          style={actionBtnStyle(false)}
        >
          ✎ 开始写作
        </button>
        <button
          type="button"
          onClick={() => navigate('/analytics')}
          style={actionBtnStyle(false)}
        >
          ↗ 查看数据
        </button>
      </div>

      {/* Recent activity */}
      <div
        style={{
          background: 'var(--v3-surface)',
          border: '1px solid var(--v3-border)',
          borderRadius: 8,
          padding: '16px 18px',
          boxShadow: 'var(--v3-shadow-card)',
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>最近动态</div>
        <div>
          {RECENT_ACTIVITY.map((a) => (
            <div
              key={a.id}
              style={{
                padding: '14px 0',
                borderBottom: '1px solid var(--v3-border-light)',
              }}
            >
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: 'var(--v3-text)',
                  marginBottom: 4,
                }}
              >
                {a.title}
              </div>
              <div
                style={{
                  fontSize: 12.5,
                  color: 'var(--v3-text-sec)',
                  display: 'flex',
                  gap: 8,
                  alignItems: 'center',
                }}
              >
                <span>{a.meta}</span>
                {a.hasRecap && (
                  <button
                    type="button"
                    onClick={() => navigate('/review')}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      padding: 0,
                      color: 'var(--v3-text)',
                      textDecoration: 'underline',
                      cursor: 'pointer',
                      fontSize: 12.5,
                      font: 'inherit',
                    }}
                  >
                    查看复盘
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI 建议 */}
      <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>AI 建议</div>
      {AI_SUGGESTIONS.map((s) => (
        <div
          key={s.id}
          style={{
            background: 'var(--v3-surface)',
            border: '1px solid var(--v3-border)',
            borderRadius: 8,
            padding: '16px 18px',
            marginTop: 12,
            boxShadow: 'var(--v3-shadow-card)',
          }}
        >
          <div
            style={{
              fontSize: 13.5,
              fontWeight: 500,
              marginBottom: 6,
              color: 'var(--v3-text)',
            }}
          >
            {s.title}
          </div>
          <div
            style={{
              fontSize: 13,
              color: 'var(--v3-text-sec)',
              lineHeight: 1.6,
              marginBottom: 8,
            }}
          >
            {s.body}{' '}
            <button
              type="button"
              onClick={() => navigate(s.link)}
              style={{
                background: 'transparent',
                border: 'none',
                padding: 0,
                color: 'var(--v3-text)',
                textDecoration: 'underline',
                cursor: 'pointer',
                fontSize: 13,
                font: 'inherit',
              }}
            >
              {s.linkText}
            </button>
          </div>
          <div
            style={{
              fontSize: 11,
              color: 'var(--v3-text-ter)',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              flexWrap: 'wrap',
            }}
          >
            <span
              style={{
                padding: '1px 6px',
                borderRadius: 3,
                background: 'var(--v3-accent-soft)',
                fontSize: 10,
                fontWeight: 600,
                color: 'var(--v3-text-sec)',
                letterSpacing: '0.5px',
              }}
            >
              AI
            </span>
            <span>{s.meta}</span>
          </div>
          <div style={{ marginTop: 8, display: 'flex', gap: 3 }}>
            <button
              type="button"
              aria-label="有帮助"
              style={fbBtnStyle()}
              onClick={() => undefined}
            >
              👍
            </button>
            <button
              type="button"
              aria-label="没帮助"
              style={fbBtnStyle()}
              onClick={() => undefined}
            >
              👎
            </button>
          </div>
        </div>
      ))}
    </PageContainer>
  );
};

interface StepProps {
  done?: boolean;
  active?: boolean;
  label: string;
}

const Step: React.FC<StepProps> = ({ done, active, label }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      fontSize: 13,
      color: 'rgba(255,255,255,0.85)',
    }}
  >
    <span
      aria-hidden="true"
      style={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        background: done
          ? 'var(--v3-green)'
          : active
            ? 'rgba(255,255,255,0.25)'
            : 'rgba(255,255,255,0.15)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 12,
        fontWeight: 600,
        flexShrink: 0,
      }}
    >
      {done ? '✓' : ''}
    </span>
    {label}
  </div>
);

const StatCard: React.FC<{
  num: string;
  label: string;
  change: { up: boolean; text: string };
}> = ({ num, label, change }) => (
  <div
    style={{
      background: 'var(--v3-surface)',
      border: '1px solid var(--v3-border)',
      borderRadius: 8,
      padding: '16px 18px',
      boxShadow: 'var(--v3-shadow-card)',
    }}
  >
    <div
      style={{
        fontSize: 26,
        fontWeight: 600,
        letterSpacing: '-0.5px',
        color: 'var(--v3-text)',
      }}
    >
      {num}
    </div>
    <div
      style={{
        fontSize: 12,
        color: 'var(--v3-text-sec)',
        marginTop: 2,
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontSize: 11.5,
        marginTop: 4,
        color: change.up ? 'var(--v3-green)' : 'var(--v3-text-sec)',
      }}
    >
      {change.text}
    </div>
  </div>
);

const actionBtnStyle = (primary: boolean): React.CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  padding: '8px 16px',
  borderRadius: 6,
  fontSize: 13,
  fontWeight: 500,
  border: '1px solid var(--v3-border)',
  background: primary ? 'var(--v3-text)' : 'var(--v3-surface)',
  color: primary ? '#fff' : 'var(--v3-text)',
  cursor: 'pointer',
  fontFamily: 'inherit',
});

const fbBtnStyle = (): React.CSSProperties => ({
  width: 24,
  height: 24,
  borderRadius: 4,
  border: '1px solid var(--v3-border)',
  background: 'var(--v3-surface)',
  cursor: 'pointer',
  fontSize: 11,
  display: 'grid',
  placeItems: 'center',
  padding: 0,
  color: 'var(--v3-text)',
  fontFamily: 'inherit',
});

export default HomePage;
