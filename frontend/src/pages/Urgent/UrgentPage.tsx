/** 急稿（原型 hifi-lumen.html 三步对齐，无新增后端）：建项目 → 进入既有内容工作台。 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { extractErrorMessage } from '@/utils/error';
import { createProject, confirmProjectIntent } from '@/services/api/v2/projects';

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const INTENT_CHIPS: Array<{ value: string; label: string }> = [
  { value: 'record', label: '记录 · 记下这个变化' },
  { value: 'share', label: '分享 · 传递感受' },
  { value: 'solve', label: '解决 · 教人方法' },
  { value: '', label: '让它判断' },
];

export default function UrgentPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [experience, setExperience] = useState('');
  const [intent, setIntent] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const project = await createProject({
        title: title.trim(),
        primary_goal: 'experiment',
        target_audience: '小红书知识/经验创作者',
        ...(intent ? { content_intent: intent as 'solve' | 'share' | 'record' } : {}),
        idempotency_key: makeKey('urgent'),
      });
      if (intent) {
        await confirmProjectIntent(project.id, {
          content_intent: intent as 'solve' | 'share' | 'record',
          audience_change: `希望读者看完获得一个真实、可判断的变化：${experience.trim().slice(0, 120)}`,
          material_requirements: [],
          expected_responses: [],
          success_signals: [],
          expected_project_version: project.version,
          idempotency_key: makeKey('urgent-intent'),
        });
      }
      navigate(`/content/${project.id}`);
    } catch (err) {
      setError(extractErrorMessage(err, '创建失败，请稍后重试'));
      setBusy(false);
    }
  };

  return (
    <div>
      {error ? <p className="login-err" role="alert">{error}</p> : null}
      <p className="kicker">急稿 · 现在就想发</p>
      <h1 className="pg">三步，十分钟内见成品。</h1>

      <div className="steps">
        <div className={`step${title.trim() ? ' done' : ''}`}>
          <span className="n">1</span>
          <div style={{ flex: 1 }}>
            <h3>这篇想说什么？</h3>
            <div className="fill">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="刚发现阳台辣椒结果了，想立刻记录这个瞬间"
                aria-label="这篇想说什么？"
              />
            </div>
          </div>
        </div>
        <div className={`step${experience.trim() ? ' done' : ''}`}>
          <span className="n">2</span>
          <div style={{ flex: 1 }}>
            <h3>一句真实经历（它只基于这个写，不编）</h3>
            <div className="fill">
              <textarea
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                placeholder="早上浇水时发现第一批发了三个果，最大的有拇指长。去年同一盆只开过花。中间只做对了一件事：人工授粉。"
                aria-label="一句真实经历（它只基于这个写，不编）"
              />
            </div>
          </div>
        </div>
        <div className={`step${intent ? ' done' : ''}`}>
          <span className="n">3</span>
          <div style={{ flex: 1 }}>
            <h3>这条内容属于哪一类？</h3>
            <p>不确定就让它判断，你确认即可。</p>
            <div className="fill intent-chips">
              {INTENT_CHIPS.map((chip) => (
                <button
                  type="button"
                  key={chip.label}
                  className={`ichip${intent === chip.value ? ' on' : ''}`}
                  onClick={() => setIntent(chip.value)}
                >
                  {chip.label}
                </button>
              ))}
            </div>
            <div className="precheck">
              <span className="ok">✓</span>
              <span>创建后先做结构预检：钩子 → 过程 → 结尾。观察窗口建议 7 天，可改。</span>
            </div>
          </div>
        </div>
      </div>

      <div className="cta" style={{ marginTop: 28 }}>
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy || !title.trim() || !experience.trim()}
          onClick={() => void submit()}
        >
          生成成品，进入发布检查
        </button>
        <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => navigate('/loop/inbox')}>
          存回收件箱，不急
        </button>
      </div>
    </div>
  );
}
