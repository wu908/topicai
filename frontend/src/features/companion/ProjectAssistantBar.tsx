/**
 * 项目助手条：自定义名称/头像（与全局 AI 分离）。
 * 头像内联渲染，避免默认导出解析歧义。
 */
import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  IconButton,
  Popover,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { EditOutlined } from '@mui/icons-material';
import {
  avatarLetter,
  avatarStyle,
  loadIdentities,
  notifyIdentities,
  updateIdentity,
  type AiIdentity,
} from './aiIdentity';

function ProjectAvatar(props: { identity: AiIdentity; size?: number }) {
  const size = props.size ?? 36;
  const identity = props.identity;
  return (
    <div
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        flexShrink: 0,
        backgroundImage: identity.avatar
          ? `url(${identity.avatar})`
          : undefined,
        background: identity.avatar ? undefined : avatarStyle(identity),
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
  );
}

export default function ProjectAssistantBar(props: { projectName?: string }) {
  const [id, setId] = useState<AiIdentity>(() => loadIdentities().project);
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [draftName, setDraftName] = useState(id.name);
  const subtitle = props.projectName
    ? `项目助手 · 只处理「${props.projectName.slice(0, 10)}…」`
    : '项目助手 · 只处理这一条内容';

  useEffect(() => {
    const sync = () => setId(loadIdentities().project);
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);

  const commitName = (name: string) => {
    const next = updateIdentity('project', {
      name: name.trim().slice(0, 12) || '项目助手',
    });
    setId(next.project);
    notifyIdentities();
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.25,
        px: 1.25,
        py: 1,
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <ProjectAvatar identity={id} />
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="subtitle2" sx={{ lineHeight: 1.2 }}>
          {id.name || '项目助手'}
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          {subtitle}
        </Typography>
      </Box>
      <IconButton
        size="small"
        aria-label="自定义项目助手"
        onClick={(e) => {
          setDraftName(id.name);
          setAnchor(e.currentTarget);
        }}
      >
        <EditOutlined fontSize="small" />
      </IconButton>
      <Popover
        open={Boolean(anchor)}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Stack spacing={1.5} sx={{ p: 2, width: 260 }}>
          <Typography variant="subtitle2">项目助手外观</Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            与全局 AI 分开保存，避免认错人。
          </Typography>
          <TextField
            size="small"
            label="名称"
            value={draftName}
            inputProps={{ maxLength: 12 }}
            onChange={(e) => setDraftName(e.target.value)}
            onBlur={() => commitName(draftName)}
          />
          <Stack direction="row" spacing={1} alignItems="center">
            <Button variant="outlined" size="small" component="label">
              上传头像
              <input
                hidden
                accept="image/*"
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const r = new FileReader();
                  r.onload = () => {
                    const next = updateIdentity('project', {
                      avatar: String(r.result),
                    });
                    setId(next.project);
                    notifyIdentities();
                  };
                  r.readAsDataURL(file);
                }}
              />
            </Button>
            <Button
              size="small"
              onClick={() => {
                const next = updateIdentity('project', { avatar: null, tone: 'c' });
                setId(next.project);
                notifyIdentities();
              }}
            >
              用默认
            </Button>
          </Stack>
          <ProjectAvatar identity={id} size={44} />
          <Button size="small" onClick={() => setAnchor(null)}>
            完成
          </Button>
        </Stack>
      </Popover>
    </Box>
  );
}
