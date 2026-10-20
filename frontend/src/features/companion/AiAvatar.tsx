/**
 * AI 头像气泡：全局 / 项目助手共用；无图时用光晕 + 首字。
 */
import type { AiIdentity } from './aiIdentity';
import { avatarLetter, avatarStyle } from './aiIdentity';

export default function AiAvatar(props: {
  identity: AiIdentity;
  size?: number;
  showName?: boolean;
  roleLabel?: string;
}) {
  const { identity, size = 36, showName = true, roleLabel } = props;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
      <div
        aria-hidden
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          flexShrink: 0,
          // 头像与光晕都走 background-image，避免简写相互覆盖。
          backgroundImage: identity.avatar
            ? `url(${identity.avatar})`
            : avatarStyle(identity),
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          border: '1px solid rgba(255,255,255,0.9)',
          boxShadow: '0 6px 16px rgba(70,95,130,0.15)',
          display: 'grid',
          placeItems: 'center',
          fontWeight: 700,
          fontSize: Math.round(size * 0.36),
          color: '#191e26',
        }}
      >
        {identity.avatar ? '' : avatarLetter(identity)}
      </div>
      {showName ? (
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 650,
              color: '#191e26',
              letterSpacing: '-0.2px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {identity.name || '助手'}
          </div>
          {roleLabel ? (
            <div style={{ fontSize: 11, color: '#7e8898', marginTop: 1 }}>{roleLabel}</div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
