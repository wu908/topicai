/**
 * 确认卡：全站唯一拍板形态（事实/意图/公开/长期经验共用外壳）。
 * 只出建议，不代拍；否决必给下一步。
 */
import { useState } from 'react';
import {
  Box,
  Button,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

export type ConfirmCardType = 'fact' | 'intent' | 'publish' | 'learning' | 'public_scope';

export interface ConfirmCardProps {
  type: ConfirmCardType;
  title: string;
  suggestion: string;
  reason?: string;
  busy?: boolean;
  /** strip = 原型项目屏底部条带；card = 默认卡片 */
  variant?: 'card' | 'strip';
  onAgree: () => void | Promise<void>;
  onChange?: (text: string) => void | Promise<void>;
  onReject?: (reason: string) => void | Promise<void>;
  /** 否决后的出路（交互地图修订 D） */
  afterReject?: Array<{ label: string; onPick: () => void }>;
}

const typeLabel: Record<ConfirmCardType, string> = {
  fact: '确认事实',
  intent: '确认意图',
  publish: '发布确认',
  public_scope: '公开范围',
  learning: '长期经验',
};

export default function ConfirmCard(props: ConfirmCardProps) {
  const [editing, setEditing] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [editText, setEditText] = useState(props.suggestion);
  const [rejectReason, setRejectReason] = useState('');
  const [done, setDone] = useState<null | 'ok' | 'chg' | 'no'>(null);
  // 写入失败时必须留在可重试状态：不能因为点了按钮就显示"已确认"。
  const [failed, setFailed] = useState<string | null>(null);

  const fail = () => setFailed('这次没有保存成功，请重试。');

  const isStrip = props.variant === 'strip';

  if (done) {
    return (
      <Box
        sx={
          isStrip
            ? {
                px: 1.25,
                py: 1,
                borderRadius: 2,
                bgcolor: 'rgba(255,255,255,0.4)',
              }
            : {
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                p: 1.5,
                bgcolor: 'rgba(255,255,255,0.35)',
              }
        }
      >
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          {done === 'ok' && '已按建议确认。可以继续下一步。'}
          {done === 'chg' && '已按你的修改确认。'}
          {done === 'no' && '已否决。选一个出路，或稍后在「今日」里继续。'}
        </Typography>
        {done === 'no' && props.afterReject?.length ? (
          <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap">
            {props.afterReject.map((a) => (
              <Button key={a.label} size="small" variant="outlined" onClick={a.onPick}>
                {a.label}
              </Button>
            ))}
          </Stack>
        ) : null}
      </Box>
    );
  }

  if (isStrip) {
    return (
      <>
        <div className="lab">
          <i aria-hidden="true" />
          确认卡 · {typeLabel[props.type] || '确认'}
        </div>
        <div className="hint">
          {props.title}。建议：{props.suggestion}
          {props.reason ? `。依据：${props.reason}` : ''}
        </div>
        {failed ? (
          <div className="hint" style={{ color: '#b4574e' }}>
            {failed}
          </div>
        ) : null}
        {!editing && !rejecting ? (
          <div className="acts">
            <button
              type="button"
              className="lumen-btn sm"
              disabled={props.busy}
              onClick={() => {
                setFailed(null);
                void Promise.resolve()
                  .then(() => props.onAgree())
                  .then(() => setDone('ok'))
                  .catch(fail);
              }}
            >
              同意
            </button>
            <button type="button" className="lumen-btn sm ghost" onClick={() => setEditing(true)}>
              改
            </button>
            <button type="button" className="lumen-btn sm ghost" onClick={() => setRejecting(true)}>
              否决
            </button>
          </div>
        ) : null}
        {editing ? (
          <div className="acts" style={{ width: '100%' }}>
            <input
              className="lumen-input"
              style={{ flex: 1, minWidth: 0 }}
              value={editText}
              aria-label="修改后的内容"
              onChange={(e) => setEditText(e.target.value)}
            />
            <button
              type="button"
              className="lumen-btn sm"
              disabled={props.busy || !editText.trim()}
              onClick={() => {
                setFailed(null);
                void Promise.resolve()
                  .then(() => props.onChange?.(editText))
                  .then(() => setDone('chg'))
                  .catch(fail);
              }}
            >
              存
            </button>
            <button type="button" className="lumen-btn sm ghost" onClick={() => setEditing(false)}>
              取消
            </button>
          </div>
        ) : null}
        {rejecting ? (
          <div className="acts" style={{ width: '100%' }}>
            <input
              className="lumen-input"
              style={{ flex: 1, minWidth: 0 }}
              placeholder="否决原因"
              value={rejectReason}
              aria-label="否决原因"
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <button
              type="button"
              className="lumen-btn sm"
              disabled={props.busy || !rejectReason.trim()}
              onClick={() => {
                setFailed(null);
                void Promise.resolve()
                  .then(() => props.onReject?.(rejectReason.trim()))
                  .then(() => setDone('no'))
                  .catch(fail);
              }}
            >
              确认
            </button>
            <button type="button" className="lumen-btn sm ghost" onClick={() => setRejecting(false)}>
              返回
            </button>
          </div>
        ) : null}
      </>
    );
  }

  return (
    <Box
      sx={{
        border: '1px solid',
        borderColor: 'rgba(143,190,232,0.35)',
        bgcolor: 'rgba(143,190,232,0.12)',
        borderRadius: 2,
        p: 1.75,
      }}
    >
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
        {typeLabel[props.type] || '确认'} · 需要你拍板
      </Typography>
      <Typography variant="subtitle2" sx={{ mt: 0.5, mb: 0.5 }}>
        {props.title}
      </Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        AI 建议：{props.suggestion}
        {props.reason ? `（依据：${props.reason}）` : ''}
      </Typography>
      {failed ? (
        <Typography variant="body2" role="status" sx={{ color: 'error.main', mt: 0.75 }}>
          {failed}
        </Typography>
      ) : null}

      {!editing && !rejecting ? (
        <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
          <Button size="small" variant="contained" disabled={props.busy} onClick={() => {
            setFailed(null);
            void Promise.resolve()
              .then(() => props.onAgree())
              .then(() => setDone('ok'))
              .catch(fail);
          }}>
            同意
          </Button>
          {props.onChange ? (
            <Button size="small" variant="outlined" onClick={() => setEditing(true)}>
              改
            </Button>
          ) : null}
          {props.onReject ? (
            <Button size="small" onClick={() => setRejecting(true)}>
              否决
            </Button>
          ) : null}
        </Stack>
      ) : null}

      {editing ? (
        <Stack spacing={1} sx={{ mt: 1.5 }}>
          <TextField
            size="small"
            multiline
            minRows={2}
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            aria-label="修改后的内容"
          />
          <Stack direction="row" spacing={1}>
            <Button
              size="small"
              variant="contained"
              disabled={props.busy || !editText.trim()}
              onClick={() => {
                setFailed(null);
                void Promise.resolve()
                  .then(() => props.onChange?.(editText))
                  .then(() => setDone('chg'))
                  .catch(fail);
              }}
            >
              保存并确认
            </Button>
            <Button size="small" onClick={() => setEditing(false)}>
              取消
            </Button>
          </Stack>
        </Stack>
      ) : null}

      {rejecting ? (
        <Stack spacing={1} sx={{ mt: 1.5 }}>
          <TextField
            size="small"
            multiline
            minRows={2}
            placeholder="为什么否决？（会记录，不会让流程卡住）"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            aria-label="否决原因"
          />
          <Stack direction="row" spacing={1}>
            <Button
              size="small"
              variant="contained"
              disabled={props.busy || !rejectReason.trim()}
              onClick={() => {
                setFailed(null);
                void Promise.resolve()
                  .then(() => props.onReject?.(rejectReason.trim()))
                  .then(() => setDone('no'))
                  .catch(fail);
              }}
            >
              确认否决
            </Button>
            <Button size="small" onClick={() => setRejecting(false)}>
              返回
            </Button>
          </Stack>
        </Stack>
      ) : null}
    </Box>
  );
}
