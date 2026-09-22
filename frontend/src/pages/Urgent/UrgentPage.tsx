/** 急稿（原型 hifi-lumen.html 三步对齐，无新增后端）：建项目 → 进入既有内容工作台。 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { extractErrorMessage } from '@/utils/error';
import { createProject, confirmProjectIntent, getProjectNextAction, respondToAction, startProject } from '@/services/api/v2/projects';

const makeKey = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

// 模式名（Step 3）：这步选的是机器怎么做，不是这条内容属于哪一类。
const INTENT_CHIPS: Array<{ value: string; label: string }> = [
  { value: 'record', label: '记过程' },
  { value: 'share', label: '讲经历' },
  { value: 'solve', label: '教方法' },
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
      // F1（用户验收测试 2026-09-19）：选了「让它判断」时，以前只 createProject、
      // 从不确认意图，用户落地在 0/5 步——「交给 AI 判断」反而比明确选一个更差。
      // 改走与内容页「新建项目」同一条 AI 推断路径：推断结果带进工作台，
      // 用户能看到「我按 X 来准备这条」并一键否决。
      if (!intent) {
        const started = await startProject({
          raw_input: `${title.trim()}\n${experience.trim()}`,
          idempotency_key: makeKey('urgent-start'),
        });
        navigate(`/content/${started.project_id}`, {
          state: { inference: started.inference },
        });
        return;
      }

      const project = await createProject({
        title: title.trim(),
        primary_goal: 'experiment',
        target_audience: '小红书知识/经验创作者',
        content_intent: intent as 'solve' | 'share' | 'record',
        idempotency_key: makeKey('urgent'),
      });
      await confirmProjectIntent(project.id, {
        content_intent: intent as 'solve' | 'share' | 'record',
        audience_change: `希望读者看完获得一个真实、可判断的变化：${experience.trim().slice(0, 120)}`,
        material_requirements: [],
        expected_responses: [],
        success_signals: [],
        expected_project_version: project.version,
        idempotency_key: makeKey('urgent-intent'),
      });
      // UX 审计 B1：第 2 步的真实经历直接回填为关键问题的回答——用户落地即
      // 处于"确认这段经历"步，不再被重复问同一个问题。回填失败不阻断创建。
      try {
        const action = await getProjectNextAction(project.id);
        if (action?.action_type === 'answer_key_question' && experience.trim()) {
          await respondToAction(action.id, {
            decision: 'accept',
            response_payload: { answer: experience.trim() },
            expected_action_version: action.version,
            idempotency_key: `urgent-answer-${action.id}-${action.version}`,
          });
        }
      } catch {
        // 预填失败仅失去一次自动回填，落地后手动补答即可。
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
      {/* F1（用户验收测试 2026-09-19）：原文写「三步，十分钟内见成品」，
          但这一步的产出是「一个已确认意图的内容项目」，成品要经过候选内容
          与发布前检查才会出现。改成本页真正交付的东西。 */}
      <h1 className="pg">三步写下真实经历，AI 接着准备候选内容。</h1>

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
            <h3>AI 按哪种方式帮你？</h3>
            <p>它决定 AI 问什么、怎么组织内容，不限制这条内容长什么样。不确定就让它判断，你确认即可。</p>
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
              {/* 结构预检发生在「发布前检查」这一步，不是创建后立刻跑；
                  原文「创建后先做结构预检」也是承诺过头，一并改正。 */}
              <span>AI 会按钩子 → 过程 → 结尾组织候选内容；发布前还会跑一次结构预检。观察窗口建议 7 天，可改。</span>
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
          开始准备候选内容
        </button>
        <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => navigate('/loop/inbox')}>
          存回收件箱，不急
        </button>
      </div>
    </div>
  );
}
