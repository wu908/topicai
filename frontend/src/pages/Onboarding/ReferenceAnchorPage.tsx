import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Chip, CircularProgress, TextField } from '@mui/material';
import { ArrowBack, AutoAwesome, EditOutlined, ThumbDownOutlined } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import {
  getReferenceAnchor,
  importReferences,
  updateReferenceAnchor,
} from '@/services/api/v2/referenceAnchor';
import type {
  AnchorCapability,
  AnchorItem,
  ReferenceAnchor,
} from '@/types/contracts/v2/referenceAnchor';
import { extractErrorMessage } from '@/utils/error';
import { parseReferences, referenceCountHint } from '@/features/reference/parseReferences';
import './ReferenceAnchorPage.css';

const PLACEHOLDER = [
  '@想成为的账号A',
  '12 平的出租屋，我按动线重排了三次',
  '结论先放前面：小空间的问题几乎都不是收纳不够……',
  '',
  '@想成为的账号B',
  '租房第一年，我把生活费降了两成',
].join('\n');

const CAPABILITY_LABEL: Record<AnchorCapability, string> = {
  structured_llm: '读懂了内容',
  deterministic_fallback: '只数了标签，没读懂内容',
  user_edited: '以你说的为准',
};

/** 一条结论由几条参考支撑——把证据摆出来，而不是只给一个置信度词。 */
function supportLabel(sampleCount: number): string {
  if (sampleCount <= 0) return '你自己写的';
  if (sampleCount === 1) return '只有 1 条参考这么说';
  return `${sampleCount} 条参考里都有`;
}

export default function ReferenceAnchorPage() {
  const navigate = useNavigate();
  const [anchor, setAnchor] = useState<ReferenceAnchor | null>(null);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [reading, setReading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [composing, setComposing] = useState(false);
  const [rewriting, setRewriting] = useState(false);
  const [draftTopics, setDraftTopics] = useState('');
  const [draftHabits, setDraftHabits] = useState('');
  const [draftAudience, setDraftAudience] = useState('');
  const importKeyRef = useRef<{ signature: string; key: string } | null>(null);
  // 卸载后到达的响应不能再写状态。
  const aliveRef = useRef(true);
  useEffect(() => () => {
    aliveRef.current = false;
  }, []);

  const parsed = useMemo(() => parseReferences(text), [text]);

  const load = useCallback(async () => {
    setError(null);
    try {
      const next = await getReferenceAnchor();
      if (!aliveRef.current) return;
      setAnchor(next);
    } catch (err) {
      if (!aliveRef.current) return;
      setError(extractErrorMessage(err, '读取参考失败'));
    } finally {
      if (aliveRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const handleRead = async () => {
    if (!parsed.items.length || parsed.problems.length) return;
    setError(null);
    setReading(true);
    try {
      const signature = text;
      if (!importKeyRef.current || importKeyRef.current.signature !== signature) {
        importKeyRef.current = { signature, key: `reference-import:${Date.now()}` };
      }
      const result = await importReferences(parsed.items, importKeyRef.current.key);
      if (result.failure_count > 0) {
        const firstFailure = result.item_results.find((item) => item.status === 'failed');
        setError(`有 ${result.failure_count} 条没能导入：${firstFailure?.error ?? '检查一下来源和标题'}`);
        return;
      }
      importKeyRef.current = null;
      setText('');
      setComposing(false);
      // 这一跳会读内容本身：模型可用时通常十几秒。
      const next = await getReferenceAnchor();
      if (!aliveRef.current) return;
      setAnchor(next);
    } catch (err) {
      if (!aliveRef.current) return;
      setError(extractErrorMessage(err, '这次没读出来，稍后再试一次'));
    } finally {
      if (aliveRef.current) setReading(false);
    }
  };

  const act = async (command: () => Promise<ReferenceAnchor>) => {
    setBusy(true);
    setError(null);
    try {
      const next = await command();
      if (aliveRef.current) setAnchor(next);
    } catch (err) {
      if (!aliveRef.current) return;
      setError(extractErrorMessage(err, '操作没有完成，请重试'));
      await load();
    } finally {
      if (aliveRef.current) setBusy(false);
    }
  };

  const reject = (value: string) =>
    act(() =>
      updateReferenceAnchor({ rejected: [value], expected_version: anchor?.version ?? 1 }),
    );

  const openRewrite = () => {
    setDraftTopics((anchor?.topics ?? []).map((item) => item.value).join('\n'));
    setDraftHabits((anchor?.structure_habits ?? []).map((item) => item.value).join('\n'));
    setDraftAudience(anchor?.audience?.value ?? '');
    setRewriting(true);
  };

  const submitRewrite = () =>
    act(async () => {
      const next = await updateReferenceAnchor({
        topics: splitLines(draftTopics),
        structure_habits: splitLines(draftHabits),
        audience: draftAudience.trim() || undefined,
        expected_version: anchor?.version ?? 1,
      });
      setRewriting(false);
      return next;
    });

  if (loading) {
    return (
      <div className="anchor-loading">
        <CircularProgress size={26} aria-label="正在读取参考" />
      </div>
    );
  }

  const hasReading = (anchor?.reference_count ?? 0) > 0;
  const showComposer = composing || !hasReading;

  return (
    <PageContainer
      title="你想做成什么样？"
      subtitle="说不出自己的定位很正常。贴 2–3 个你想做成的账号或笔记，我们替你读它们的选题、写法和读者。"
    >
      <Button className="anchor-back" startIcon={<ArrowBack />} color="inherit" onClick={() => navigate('/me')}>
        返回我的
      </Button>
      {error ? (
        <Alert severity="error" role="alert" action={<Button onClick={() => void load()}>重试</Button>}>
          {error}
        </Alert>
      ) : null}

      {reading ? (
        <section className="anchor-section" aria-labelledby="anchor-reading-title">
          <div className="anchor-block-head">
            <CircularProgress size={18} />
            <h2 id="anchor-reading-title">正在读这 {parsed.items.length || anchor?.reference_count} 条参考…</h2>
          </div>
          <p className="anchor-note" role="status">
            这一步会读内容本身，通常十几秒。你可以先去做别的——读数会留下来，回来直接看。
          </p>
        </section>
      ) : null}

      {showComposer && !reading ? (
        <section className="anchor-section" aria-labelledby="anchor-compose-title">
          <div className="anchor-heading">
            {hasReading ? <span>再加几条</span> : <span>第 1 步</span>}
            <h2 id="anchor-compose-title">贴 2–3 个你想做成的样子</h2>
          </div>
          <TextField
            label="参考内容"
            value={text}
            onChange={(event) => setText(event.target.value)}
            multiline
            minRows={8}
            placeholder={PLACEHOLDER}
            helperText="一条一段：第一行是 @账号名，接着是标题，再下面是正文（只贴开头也行）"
          />
          {parsed.items.length ? (
            <div className="anchor-preview">
              <strong>已识别 {parsed.items.length} 条参考</strong>
              <div className="anchor-chips">
                {parsed.items.map((item, index) => (
                  <Chip
                    key={`${item.source_handle}-${index}`}
                    size="small"
                    variant="outlined"
                    label={`${item.source_handle || '未写来源'} · ${item.title.slice(0, 14)}`}
                  />
                ))}
              </div>
              <span className="anchor-note">{referenceCountHint(parsed.items.length)}</span>
            </div>
          ) : null}
          {parsed.problems.map((problem) => (
            <Alert severity="warning" key={problem}>{problem}</Alert>
          ))}
          <div className="anchor-actions">
            <Button
              variant="contained"
              startIcon={<AutoAwesome />}
              disabled={busy || !parsed.items.length || parsed.problems.length > 0}
              onClick={() => void handleRead()}
            >
              读这些参考
            </Button>
            {hasReading ? (
              <Button color="inherit" disabled={busy} onClick={() => setComposing(false)}>收起</Button>
            ) : null}
          </div>
        </section>
      ) : null}

      {hasReading && !reading ? (
        <section className="anchor-section" aria-labelledby="anchor-read-title">
          <div className="anchor-heading">
            <span>从你贴的 {anchor?.reference_count} 条参考里读出来的</span>
            <h2 id="anchor-read-title">你想做成什么样</h2>
            <Chip size="small" label={CAPABILITY_LABEL[anchor?.capability ?? 'deterministic_fallback']} />
          </div>
          {anchor?.source_handles.length ? (
            <p className="anchor-note">参考来自：{anchor.source_handles.join('、')}</p>
          ) : null}

          <AnchorBlock
            title="选题范围"
            hint="这个内容空间在讲什么"
            items={anchor?.topics ?? []}
            busy={busy}
            onReject={reject}
          />
          <AnchorBlock
            title="这类内容怎么写"
            hint="开头、篇幅、结构上的做法"
            items={anchor?.structure_habits ?? []}
            busy={busy}
            onReject={reject}
          />
          {anchor?.audience ? (
            <AnchorBlock
              title="谁在看这类内容"
              hint="这类内容的读者"
              items={[anchor.audience]}
              busy={busy}
              onReject={reject}
            />
          ) : (
            <div className="anchor-empty-block">
              <h3>谁在看这类内容</h3>
              <p className="anchor-note">这条没能从参考里读出来。它需要你自己定——在下面「我自己写」里填。</p>
            </div>
          )}

          {(anchor?.limitations ?? []).length ? (
            <ul className="anchor-limitations">
              {anchor?.limitations.map((item) => <li key={item}>{item}</li>)}
            </ul>
          ) : null}

          <div className="anchor-actions">
            <Button startIcon={<EditOutlined />} disabled={busy} onClick={openRewrite}>
              {rewriting ? '正在写…' : '都不对？我自己写'}
            </Button>
            <Button color="inherit" disabled={busy} onClick={() => setComposing(true)}>再贴几条</Button>
          </div>

          {rewriting ? (
            <div className="anchor-rewrite">
              <TextField
                label="选题范围"
                value={draftTopics}
                onChange={(event) => setDraftTopics(event.target.value)}
                multiline
                minRows={3}
                helperText="每行一项，最多 5 项"
              />
              <TextField
                label="这类内容怎么写"
                value={draftHabits}
                onChange={(event) => setDraftHabits(event.target.value)}
                multiline
                minRows={3}
                helperText="每行一项，最多 5 项"
              />
              <TextField
                label="谁在看这类内容"
                value={draftAudience}
                onChange={(event) => setDraftAudience(event.target.value)}
              />
              <p className="anchor-note">
                以你说的为准：保存之后，再贴新的参考也不会覆盖你自己的判断。
              </p>
              <div className="anchor-actions">
                <Button variant="contained" disabled={busy} onClick={() => void submitRewrite()}>
                  以我说的为准
                </Button>
                <Button color="inherit" disabled={busy} onClick={() => setRewriting(false)}>取消</Button>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {hasReading && !reading ? (
        <div className="anchor-next">
          <Button variant="contained" disabled={busy} onClick={() => navigate('/content')}>
            开始写第一条内容
          </Button>
          <span className="anchor-note">这条读数会留着，写的时候用得上。</span>
        </div>
      ) : null}
    </PageContainer>
  );
}

function AnchorBlock({
  title,
  hint,
  items,
  busy,
  onReject,
}: {
  title: string;
  hint: string;
  items: AnchorItem[];
  busy: boolean;
  onReject: (value: string) => Promise<void>;
}) {
  if (!items.length) return null;
  return (
    <div className="anchor-block">
      <div className="anchor-block-head">
        <h3>{title}</h3>
        <span className="anchor-hint">{hint}</span>
      </div>
      <ul>
        {items.map((item) => (
          <li key={item.value}>
            <div className="anchor-item-main">
              <strong>{item.value}</strong>
              <span className="anchor-support">{supportLabel(item.sample_count)}</span>
            </div>
            {item.limitations.map((limitation) => (
              <span className="anchor-item-limitation" key={limitation}>{limitation}</span>
            ))}
            <Button
              size="small"
              color="inherit"
              startIcon={<ThumbDownOutlined />}
              disabled={busy}
              onClick={() => void onReject(item.value)}
            >
              不对
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function splitLines(value: string): string[] {
  return [...new Set(value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean))].slice(0, 5);
}
