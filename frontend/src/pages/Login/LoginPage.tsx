/**
 * Login / Register page — V3 design (topicai-v3-login-meta.html).
 * Two-column layout: 380px form (left) + 480px brand panel (right).
 * Tabs switch between 登录 and 注册. 注册 has an extra 平台 select.
 * Social login buttons (微信 / 手机) are decorative; the backend OAuth
 * endpoints are not yet implemented so they log a console warning and
 * do not navigate.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

type TabValue = 'login' | 'register';

const PLATFORMS = [
  { value: '', label: '选择平台' },
  { value: 'wechat-mp', label: '微信公众号' },
  { value: 'xhs', label: '小红书' },
  { value: 'wechat-video', label: '视频号' },
  { value: 'bilibili', label: 'B 站' },
  { value: 'douyin', label: '抖音' },
  { value: 'zhihu', label: '知乎' },
];

const FEATURES = [
  { icon: '✦', label: 'AI 选题推荐 — 基于实时热点与你的定位精准匹配' },
  { icon: '✎', label: '智能写作助手 — 6 种 AI 工具提升创作效率' },
  { icon: '◉', label: '爆款内容拆解 — 学习高传播内容的底层结构' },
  { icon: '↗', label: '全链路数据分析 — 从发布到复盘一站式洞察' },
  { icon: '⏱', label: '最佳发布时机 — 粉丝活跃数据驱动排期建议' },
];

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [tab, setTab] = useState<TabValue>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [platform, setPlatform] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [socialPending, setSocialPending] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    clearError();
    try {
      if (tab === 'login') {
        await login(email, password);
      } else {
        await register(email, username, password);
      }
      navigate('/');
    } catch {
      // Error is rendered from the store; nothing else to do here.
    }
  };

  const handleSocialLogin = (provider: 'wechat' | 'phone'): void => {
    setSocialPending(provider);
    // eslint-disable-next-line no-console
    console.warn(`[LoginPage] ${provider} OAuth not implemented in backend`);
  };

  return (
    <div
      style={{
        display: 'flex',
        width: '100%',
        height: '100vh',
        overflow: 'hidden',
      }}
    >
      {/* Left — form */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--v3-bg)',
          position: 'relative',
        }}
      >
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(135deg, rgba(44,44,44,0.02) 0%, rgba(44,44,44,0.04) 100%)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            width: 380,
            position: 'relative',
            zIndex: 1,
          }}
        >
          <div
            style={{
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: '-0.5px',
              marginBottom: 8,
              color: 'var(--v3-text)',
            }}
          >
            TopicAI
          </div>
          <div
            style={{
              fontSize: 14,
              color: 'var(--v3-text-sec)',
              marginBottom: 36,
            }}
          >
            AI 驱动的内容创作运营平台
          </div>

          {/* Tabs */}
          <div
            role="tablist"
            style={{
              display: 'flex',
              gap: 0,
              marginBottom: 28,
              borderBottom: '1px solid var(--v3-border)',
            }}
          >
            {(['login', 'register'] as TabValue[]).map((value) => {
              const active = tab === value;
              const label = value === 'login' ? '登录' : '注册';
              return (
                <button
                  key={value}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => {
                    setTab(value);
                    clearError();
                  }}
                  style={{
                    padding: '10px 20px',
                    fontSize: 14,
                    fontWeight: 500,
                    color: active ? 'var(--v3-text)' : 'var(--v3-text-sec)',
                    background: 'transparent',
                    border: 'none',
                    borderBottom: active ? '2px solid var(--v3-text)' : '2px solid transparent',
                    marginBottom: -1,
                    cursor: 'pointer',
                    transition: 'color 0.15s',
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {/* Error alert */}
          {error && (
            <div
              role="alert"
              style={{
                fontSize: 12.5,
                color: 'var(--v3-red)',
                marginBottom: 8,
              }}
            >
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} noValidate>
            <div style={{ marginBottom: 18 }}>
              <label
                htmlFor="login-email"
                style={{
                  display: 'block',
                  fontSize: 12.5,
                  fontWeight: 500,
                  color: 'var(--v3-text-sec)',
                  marginBottom: 6,
                }}
              >
                邮箱地址
              </label>
              <input
                id="login-email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  height: 42,
                  fontSize: 14,
                  padding: '0 14px',
                  width: '100%',
                  borderRadius: 6,
                  border: '1px solid var(--v3-border)',
                  background: 'var(--v3-bg)',
                  color: 'var(--v3-text)',
                  fontFamily: 'inherit',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--v3-text)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--v3-border)';
                }}
              />
            </div>

            {tab === 'register' && (
              <>
                <div style={{ marginBottom: 18 }}>
                  <label
                    htmlFor="login-username"
                    style={{
                      display: 'block',
                      fontSize: 12.5,
                      fontWeight: 500,
                      color: 'var(--v3-text-sec)',
                      marginBottom: 6,
                    }}
                  >
                    姓名
                  </label>
                  <input
                    id="login-username"
                    type="text"
                    placeholder="你的姓名"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    minLength={3}
                    maxLength={50}
                    style={{
                      height: 42,
                      fontSize: 14,
                      padding: '0 14px',
                      width: '100%',
                      borderRadius: 6,
                      border: '1px solid var(--v3-border)',
                      background: 'var(--v3-bg)',
                      color: 'var(--v3-text)',
                      fontFamily: 'inherit',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = 'var(--v3-text)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = 'var(--v3-border)';
                    }}
                  />
                </div>

                <div style={{ marginBottom: 18 }}>
                  <label
                    htmlFor="login-platform"
                    style={{
                      display: 'block',
                      fontSize: 12.5,
                      fontWeight: 500,
                      color: 'var(--v3-text-sec)',
                      marginBottom: 6,
                    }}
                  >
                    你的主要创作平台
                  </label>
                  <select
                    id="login-platform"
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      height: 42,
                      fontSize: 14,
                      padding: '0 12px',
                      borderRadius: 6,
                      border: '1px solid var(--v3-border)',
                      background: 'var(--v3-surface)',
                      color: 'var(--v3-text)',
                      fontFamily: 'inherit',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = 'var(--v3-text)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = 'var(--v3-border)';
                    }}
                  >
                    {PLATFORMS.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            <div style={{ marginBottom: 18 }}>
              <label
                htmlFor="login-password"
                style={{
                  display: 'block',
                  fontSize: 12.5,
                  fontWeight: 500,
                  color: 'var(--v3-text-sec)',
                  marginBottom: 6,
                }}
              >
                密码
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder={tab === 'register' ? '至少 8 位字符' : '输入密码'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  style={{
                    height: 42,
                    fontSize: 14,
                    padding: '0 60px 0 14px',
                    width: '100%',
                    borderRadius: 6,
                    border: '1px solid var(--v3-border)',
                    background: 'var(--v3-bg)',
                    color: 'var(--v3-text)',
                    fontFamily: 'inherit',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = 'var(--v3-text)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'var(--v3-border)';
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? '隐藏密码' : '显示密码'}
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: 9,
                    height: 24,
                    width: 28,
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--v3-text-sec)',
                    fontSize: 12,
                  }}
                >
                  {showPassword ? '隐藏' : '显示'}
                </button>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 4,
              }}
            >
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: 12.5,
                  color: 'var(--v3-text-sec)',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  style={{ accentColor: 'var(--v3-text)' }}
                />
                记住我
              </label>
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  // No password recovery endpoint implemented yet.
                  // eslint-disable-next-line no-console
                  console.warn('[LoginPage] password recovery not implemented');
                }}
                style={{
                  fontSize: 12.5,
                  color: 'var(--v3-text)',
                  textDecoration: 'underline',
                }}
              >
                忘记密码？
              </a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                width: '100%',
                height: 44,
                background: 'var(--v3-text)',
                color: '#fff',
                border: 'none',
                borderRadius: 6,
                fontSize: 15,
                fontWeight: 500,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1,
                marginTop: 8,
                fontFamily: 'inherit',
              }}
            >
              {isLoading ? '处理中...' : tab === 'login' ? '登录' : '创建账号'}
            </button>
          </form>

          {/* Divider */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              margin: '24px 0',
              fontSize: 12,
              color: 'var(--v3-text-ter)',
            }}
          >
            <span style={{ flex: 1, height: 1, background: 'var(--v3-border)' }} />
            或
            <span style={{ flex: 1, height: 1, background: 'var(--v3-border)' }} />
          </div>

          {/* Social login */}
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              type="button"
              onClick={() => handleSocialLogin('wechat')}
              disabled={socialPending !== null}
              style={{
                flex: 1,
                height: 42,
                border: '1px solid var(--v3-border)',
                borderRadius: 6,
                background: 'var(--v3-surface)',
                cursor: socialPending === 'wechat' ? 'wait' : 'pointer',
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--v3-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
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
              <span aria-hidden="true" style={{ fontSize: 16, fontWeight: 700 }}>微</span>
              {socialPending === 'wechat' ? '跳转中...' : '微信登录'}
            </button>
            <button
              type="button"
              onClick={() => handleSocialLogin('phone')}
              disabled={socialPending !== null}
              style={{
                flex: 1,
                height: 42,
                border: '1px solid var(--v3-border)',
                borderRadius: 6,
                background: 'var(--v3-surface)',
                cursor: socialPending === 'phone' ? 'wait' : 'pointer',
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--v3-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
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
              <span aria-hidden="true" style={{ fontSize: 16 }}>📱</span>
              {socialPending === 'phone' ? '发送中...' : '手机验证码'}
            </button>
          </div>

          {/* Terms */}
          <div
            style={{
              marginTop: 24,
              fontSize: 12.5,
              color: 'var(--v3-text-sec)',
              textAlign: 'center',
            }}
          >
            登录即代表同意{' '}
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              style={{ color: 'var(--v3-text)', textDecoration: 'underline' }}
            >
              服务条款
            </a>{' '}
            和{' '}
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              style={{ color: 'var(--v3-text)', textDecoration: 'underline' }}
            >
              隐私政策
            </a>
          </div>
        </div>
      </div>

      {/* Right — brand panel */}
      <aside
        style={{
          width: 480,
          background: 'var(--v3-text)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: 60,
          color: '#fff',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Decorative blobs */}
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            right: -80,
            bottom: -80,
            width: 320,
            height: 320,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.04)',
          }}
        />
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            right: 40,
            top: -40,
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.03)',
          }}
        />

        <h2
          style={{
            fontSize: 32,
            fontWeight: 700,
            marginBottom: 12,
            letterSpacing: '-0.5px',
            lineHeight: 1.25,
            position: 'relative',
          }}
        >
          让 AI 成为你的
          <br />
          内容运营搭档
        </h2>
        <p
          style={{
            fontSize: 15,
            color: 'rgba(255,255,255,0.75)',
            lineHeight: 1.6,
            marginBottom: 28,
            position: 'relative',
            margin: '0 0 28px 0',
          }}
        >
          从选题发现、AI 写作、标题优化到数据分析，TopicAI 帮助内容创作者用数据驱动每一个决策。
        </p>

        <ul
          style={{
            listStyle: 'none',
            padding: 0,
            margin: 0,
            position: 'relative',
          }}
        >
          {FEATURES.map((f) => (
            <li
              key={f.label}
              style={{
                fontSize: 14,
                color: 'rgba(255,255,255,0.85)',
                padding: '10px 0',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                borderBottom: '1px solid rgba(255,255,255,0.1)',
              }}
            >
              <span
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: 'rgba(255,255,255,0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 14,
                  flexShrink: 0,
                }}
                aria-hidden="true"
              >
                {f.icon}
              </span>
              {f.label}
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
};

export default LoginPage;
