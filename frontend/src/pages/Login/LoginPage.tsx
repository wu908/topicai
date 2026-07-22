/**
 * Login / Register page — V3 design (topicai-v3-login-meta.html).
 * Two-column layout: 380px form (left) + 480px brand panel (right).
 * Tabs switch between 登录 and 注册 for the Xiaohongshu-focused MVP.
 * Only implemented authentication methods are presented.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

type TabValue = 'login' | 'register';

const FEATURES = [
  { icon: '1', label: '确认这条内容想给读者带来的变化' },
  { icon: '2', label: '补齐你亲自经历过的事实和素材' },
  { icon: '3', label: '逐段确认候选内容与公开范围' },
  { icon: '4', label: '发布后只保留一个下一轮实验' },
];

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [tab, setTab] = useState<TabValue>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

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
              letterSpacing: 0,
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
            小红书知识与经验创作者的内容操作系统
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
          <form onSubmit={handleSubmit}>
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
                justifyContent: 'flex-start',
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

          {/* Terms */}
          <div
            style={{
              marginTop: 24,
              fontSize: 12.5,
              color: 'var(--v3-text-sec)',
              textAlign: 'center',
            }}
          >
            当前 MVP 仅支持邮箱登录与注册
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
        <h2
          style={{
            fontSize: 32,
            fontWeight: 700,
            marginBottom: 12,
            letterSpacing: 0,
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
            position: 'relative',
            margin: '0 0 28px 0',
          }}
        >
          AI 负责理解意图、找到证据缺口并准备下一步；你只确认事实、表达与不可逆决定。
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
