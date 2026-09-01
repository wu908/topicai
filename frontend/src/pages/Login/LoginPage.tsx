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

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [tab, setTab] = useState<TabValue>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  // 审计修复 2026-08-16 UX-H1/M8：不再依赖浏览器原生 minLength 气泡，
  // 改用中文表单校验提示；本地校验错误优先于 store 错误展示。
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    clearError();
    setFormError(null);
    if (tab === 'register') {
      if (username.trim().length < 2) {
        setFormError('姓名至少需要 2 个字符，两个字的中文姓名也可以。');
        return;
      }
      if (password.length < 8) {
        setFormError('密码至少需要 8 位字符。');
        return;
      }
      if (confirmPassword !== password) {
        setFormError('两次输入的密码不一致，请检查后重新提交。');
        return;
      }
    }
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
        minHeight: '100dvh',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <div
        style={{
          width: 400,
          borderRadius: 22,
          border: '1px solid rgba(255,255,255,.8)',
          outline: '1px solid rgba(23,28,38,.055)',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 22px 60px rgba(70,95,130,.14)',
          background: 'rgba(255,255,255,.55)',
          backdropFilter: 'blur(26px) saturate(155%)',
          padding: '32px 36px 28px',
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
                    setFormError(null);
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
          {(formError || error) && (
            <div
              role="alert"
              style={{
                fontSize: 12.5,
                color: 'var(--v3-red)',
                marginBottom: 8,
              }}
            >
              {formError || error}
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
                  background: 'rgba(255,255,255,.5)',
          backdropFilter: 'blur(26px) saturate(155%)',
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
                    maxLength={50}
                    style={{
                      height: 42,
                      fontSize: 14,
                      padding: '0 14px',
                      width: '100%',
                      borderRadius: 6,
                      border: '1px solid var(--v3-border)',
                      background: 'rgba(255,255,255,.5)',
          backdropFilter: 'blur(26px) saturate(155%)',
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
                  // 审计修复 UX-M8：长度策略改为提交时中文提示，
                  // 避免浏览器原生英文校验气泡。
                  style={{
                    height: 42,
                    fontSize: 14,
                    padding: '0 60px 0 14px',
                    width: '100%',
                    borderRadius: 6,
                    border: '1px solid var(--v3-border)',
                    background: 'rgba(255,255,255,.5)',
          backdropFilter: 'blur(26px) saturate(155%)',
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
              {tab === 'register' && (
                <div style={{ fontSize: 12, color: 'var(--v3-text-sec)', marginTop: 6 }}>
                  密码至少需要 8 位字符
                </div>
              )}
            </div>

            {tab === 'register' && (
              <div style={{ marginBottom: 18 }}>
                <label
                  htmlFor="login-confirm-password"
                  style={{
                    display: 'block',
                    fontSize: 12.5,
                    fontWeight: 500,
                    color: 'var(--v3-text-sec)',
                    marginBottom: 6,
                  }}
                >
                  确认密码
                </label>
                <input
                  id="login-confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="再输入一次密码"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  style={{
                    height: 42,
                    fontSize: 14,
                    padding: '0 14px',
                    width: '100%',
                    borderRadius: 6,
                    border: '1px solid var(--v3-border)',
                    background: 'rgba(255,255,255,.5)',
          backdropFilter: 'blur(26px) saturate(155%)',
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
            )}

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


    </div>
  );
};

export default LoginPage;
