/**
 * 设置（整页）：产品 / 全局 AI / 项目助手 / 记忆 / 隐私
 * 短项即改即存；长文本（agent.md）点保存。
 */
import { useCallback, useEffect, useState, type ChangeEvent } from 'react';
import {
  Alert,
  Button,
  TextField,
} from '@mui/material';
import {
  getUserSettings,
  updateUserSettings,
} from '@/services/api/v2/projects';
import type { UserSettings } from '@/types/contracts/v2/content';
import {
  loadIdentities,
  notifyIdentities,
  updateIdentity,
} from '@/features/companion/aiIdentity';
import { extractErrorMessage } from '@/utils/error';

type SectionId = 'prod' | 'gai' | 'pai' | 'mem' | 'priv';

const SECTIONS: Array<{ id: SectionId; title: string; sub: string; chip: string }> = [
  { id: 'prod', title: '产品与创作', sub: '整站行为：形态、节奏、检查、对账提醒', chip: '产品' },
  { id: 'gai', title: '全局 AI（悬浮球）', sub: '灵感速记 + 全站操控；与项目助手设置分开', chip: '全局 AI' },
  { id: 'pai', title: '项目助手（内容页）', sub: '只服务「当前这一条内容」；与全局 AI 分开配置', chip: '项目助手' },
  { id: 'mem', title: '记忆文档', sub: '路径画像、判断记忆、用户偏好', chip: '记忆' },
  { id: 'priv', title: '隐私与数据', sub: '素材默认级别、导出、删除', chip: '隐私' },
];

/** 原型 .sel 下拉 */
function Sel(props: {
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
  ariaLabel?: string;
}) {
  return (
    <select
      className="sel"
      value={props.value}
      aria-label={props.ariaLabel}
      onChange={(e) => props.onChange(e.target.value)}
    >
      {props.options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

function Row(props: {
  label: string;
  hint?: string;
  control: React.ReactNode;
}) {
  return (
    <div className="lumen-row" style={{ cursor: 'default' }}>
      <div className="body">
        <div className="title">{props.label}</div>
        {props.hint ? <div className="meta">{props.hint}</div> : null}
      </div>
      {props.control}
    </div>
  );
}

export default function SettingsPage() {
  const [section, setSection] = useState<SectionId>('prod');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);

  const [gaiName, setGaiName] = useState('');
  const [paiName, setPaiName] = useState('');
  const [globalAgent, setGlobalAgent] = useState('');
  const [projectAgent, setProjectAgent] = useState('');

  const say = (msg: string) => {
    setFlash(msg);
    window.setTimeout(() => setFlash(null), 1800);
  };

  const applyToIdentity = (s: UserSettings) => {
    const agent = s.agent_identity || {};
    setGaiName(agent.global_name ?? loadIdentities().global.name);
    setPaiName(agent.project_name ?? loadIdentities().project.name);
    setGlobalAgent(agent.global_agent_md ?? '');
    setProjectAgent(agent.project_agent_md ?? '');
    if (agent.global_name || agent.global_avatar) {
      updateIdentity('global', {
        ...(agent.global_name ? { name: agent.global_name } : {}),
        ...(agent.global_avatar ? { avatar: agent.global_avatar } : {}),
      });
      notifyIdentities();
    }
    if (agent.project_name || agent.project_avatar) {
      updateIdentity('project', {
        ...(agent.project_name ? { name: agent.project_name } : {}),
        ...(agent.project_avatar ? { avatar: agent.project_avatar } : {}),
      });
      notifyIdentities();
    }
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await getUserSettings();
      setSettings(s);
      applyToIdentity(s);
    } catch (e) {
      setError(extractErrorMessage(e, '设置加载失败，请重试'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const save = async (patch: {
    agent_identity?: Record<string, unknown>;
    product_prefs?: Record<string, unknown>;
  }) => {
    if (!settings) return;
    setSaving(true);
    setError(null);
    try {
      const next = await updateUserSettings({
        weekly_publish_goal: settings.weekly_publish_goal,
        content_strategy: settings.content_strategy,
        xiaohongshu_account_reference: settings.xiaohongshu_account_reference ?? undefined,
        consent: settings.consent,
        auto_digest_enabled: settings.auto_digest_enabled,
        agent_identity: patch.agent_identity,
        product_prefs: patch.product_prefs,
        expected_version: settings.version,
      });
      setSettings(next);
      applyToIdentity(next);
      say('已保存');
    } catch (e) {
      setError(extractErrorMessage(e, '保存失败，请重试'));
    } finally {
      setSaving(false);
    }
  };

  const onAvatar = (who: 'gai' | 'pai') => (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const r = new FileReader();
    r.onload = () => {
      const url = String(r.result);
      updateIdentity(who === 'gai' ? 'global' : 'project', { avatar: url });
      notifyIdentities();
      void save({
        agent_identity:
          who === 'gai' ? { global_avatar: url } : { project_avatar: url },
      });
    };
    r.readAsDataURL(file);
  };

  if (loading) {
    return (
      <div>
        <div className="lumen-topbar">
          <div>
            <h1>设置</h1>
            <p className="sub" style={{ margin: 0 }}>正在读取…</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="lumen-topbar">
        <div>
          <h1>设置</h1>
          <p className="sub" style={{ margin: 0 }}>
            产品 · 全局 AI · 项目助手
          </p>
        </div>
        {flash ? (
          <span style={{ color: '#2e9e5b', fontSize: 12 }}>{flash}</span>
        ) : null}
      </div>

      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

      {/* 原型：单 band + chips 跳段 + 连续行 */}
      <div className="lumen-band grow">
        <div className="lumen-band-h">
          <h2>设置</h2>
          <div className="tools" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {SECTIONS.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`lumen-chip${section === s.id ? ' on' : ''}`}
                data-jump={s.id}
                onClick={() => {
                  setSection(s.id);
                  document.getElementById(`sec-${s.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }}
              >
                {s.chip}
              </button>
            ))}
          </div>
        </div>

        {SECTIONS.map((s) => (
          <div key={s.id}>
            {/* 段头：全宽行（原型 sec-*） */}
            <div
              id={`sec-${s.id}`}
              className="lumen-row"
              style={{ cursor: 'default', alignItems: 'flex-start', scrollMarginTop: 16, borderTop: s.id === 'prod' ? 'none' : undefined }}
            >
              <div className="body" style={{ width: '100%' }}>
                <div className="title">{s.title}</div>
                <div className="meta">{s.sub}</div>
              </div>
            </div>

            {s.id === 'prod' && (
                <>
                  <Row
                    label="默认内容形态"
                    hint="新建条目默认类型，可逐条改"
                    control={
                      <Sel
                        value={settings?.product_prefs?.default_content_kind ?? 'graphic_note'}
                        options={[
                          { value: 'graphic_note', label: '图文' },
                          { value: 'vlog_plan', label: '视频 / vlog' },
                        ]}
                        onChange={(v) => void save({ product_prefs: { default_content_kind: v as 'graphic_note' | 'vlog_plan' } })}
                      />
                    }
                  />
                  <Row
                    label="每周目标"
                    hint="只用于节奏提醒，不是硬指标"
                    control={
                      <Sel
                        value={String(settings?.weekly_publish_goal ?? 2)}
                        options={[
                          { value: '1', label: '1–2 条' },
                          { value: '3', label: '3–4 条' },
                          { value: '0', label: '不定' },
                        ]}
                        onChange={(v) => {
                          if (!settings) return;
                          void (async () => {
                            setSaving(true);
                            try {
                              const next = await updateUserSettings({
                                weekly_publish_goal: Number(v) || 1,
                                content_strategy: settings.content_strategy,
                                consent: settings.consent,
                                expected_version: settings.version,
                              });
                              setSettings(next);
                              say('已保存');
                            } catch (e) {
                              setError(extractErrorMessage(e, '保存失败'));
                            } finally {
                              setSaving(false);
                            }
                          })();
                        }}
                      />
                    }
                  />
                  <Row
                    label="发前检查"
                    hint="敏感词、事实来源等；严格更慢更稳"
                    control={
                      <Sel
                        value={settings?.product_prefs?.publish_check_level ?? 'standard'}
                        options={[
                          { value: 'standard', label: '标准' },
                          { value: 'strict', label: '严格' },
                          { value: 'soft', label: '仅提醒' },
                        ]}
                        onChange={(v) => void save({ product_prefs: { publish_check_level: v as 'standard' | 'strict' | 'soft' } })}
                      />
                    }
                  />
                  <Row
                    label="对账提醒"
                    hint="发布后多久提醒你回填数据"
                    control={
                      <Sel
                        value={String(settings?.product_prefs?.retro_reminder_days ?? 3)}
                        options={[
                          { value: '3', label: '3 天' },
                          { value: '7', label: '7 天' },
                          { value: '0', label: '不提醒' },
                        ]}
                        onChange={(v) => void save({ product_prefs: { retro_reminder_days: Number(v) } })}
                      />
                    }
                  />
                </>
              )}

              {s.id === 'gai' && (
                <>
                  <Row
                    label="名称"
                    hint="全局助手显示名"
                    control={
                      <input
                        className="inp"
                        type="text"
                        value={gaiName}
                        maxLength={12}
                        onChange={(e) => setGaiName(e.target.value)}
                        onBlur={() => void save({ agent_identity: { global_name: gaiName } })}
                      />
                    }
                  />
                  <Row
                    label="头像"
                    hint="可上传图片；默认不公开"
                    control={
                      <Button variant="outlined" component="label" size="small">
                        上传图片
                        <input hidden accept="image/*" type="file" onChange={onAvatar('gai')} />
                      </Button>
                    }
                  />
                  <Row
                    label="agent.md · 全局指令"
                    hint="称呼、语气、如何帮你操作。不覆盖「四决策由你拍板」。"
                    control={
                      <Button
                        size="small"
                        variant="outlined"
                        disabled={saving}
                        onClick={() => void save({ agent_identity: { global_agent_md: globalAgent } })}
                      >
                        编辑指令
                      </Button>
                    }
                  />
                  <TextField
                    multiline
                    minRows={3}
                    fullWidth
                    value={globalAgent}
                    onChange={(e) => setGlobalAgent(e.target.value)}
                    sx={{ my: 1.5, mx: 2, width: 'calc(100% - 32px)' }}
                  />
                  <Row
                    label="模型与接口"
                    hint="Base URL / API Key / 模型名 · 只存本机"
                    control={
                      <Button size="small" variant="outlined">
                        配置模型…
                      </Button>
                    }
                  />
                  <Row
                    label="灵感快捷键"
                    hint="按住说话或快捷唤起全局 AI"
                    control={
                      <Sel
                        value="alt"
                        options={[
                          { value: 'alt', label: 'Alt + Space' },
                          { value: 'ball', label: '仅悬浮球' },
                        ]}
                        onChange={() => say('已保存')}
                      />
                    }
                  />
                  <Row
                    label="全局操控范围"
                    hint="允许全局 AI 代办哪些操作（发布等仍确认）"
                    control={
                      <Button size="small" variant="outlined">
                        管理权限…
                      </Button>
                    }
                  />
                </>
              )}

              {s.id === 'pai' && (
                <>
                  <Row
                    label="名称"
                    hint="项目对话里的显示名"
                    control={
                      <input
                        className="inp"
                        type="text"
                        value={paiName}
                        maxLength={12}
                        onChange={(e) => setPaiName(e.target.value)}
                        onBlur={() => void save({ agent_identity: { project_name: paiName } })}
                      />
                    }
                  />
                  <Row
                    label="头像"
                    hint="可上传图片；与全局 AI 区分，避免混淆"
                    control={
                      <Button variant="outlined" component="label" size="small">
                        上传图片
                        <input hidden accept="image/*" type="file" onChange={onAvatar('pai')} />
                      </Button>
                    }
                  />
                  <Row
                    label="agent.md · 项目指令"
                    hint="只谈这条稿；不发散到其他项目"
                    control={
                      <Button
                        size="small"
                        variant="outlined"
                        disabled={saving}
                        onClick={() => void save({ agent_identity: { project_agent_md: projectAgent } })}
                      >
                        编辑指令
                      </Button>
                    }
                  />
                  <TextField
                    multiline
                    minRows={3}
                    fullWidth
                    value={projectAgent}
                    onChange={(e) => setProjectAgent(e.target.value)}
                    sx={{ my: 1.5, mx: 2, width: 'calc(100% - 32px)' }}
                  />
                  <Row
                    label="去 AI 味（成稿）"
                    hint="改得更像人话；不改事实。仅作用于内容稿"
                    control={
                      <button
                        type="button"
                        className={`lumen-chip${(settings?.product_prefs?.humanize_enabled ?? true) ? ' on' : ''}`}
                        aria-label="项目去AI味"
                        aria-pressed={settings?.product_prefs?.humanize_enabled ?? true}
                        onClick={() =>
                          void save({
                            product_prefs: {
                              humanize_enabled: !(settings?.product_prefs?.humanize_enabled ?? true),
                            },
                          })
                        }
                      >
                        {(settings?.product_prefs?.humanize_enabled ?? true) ? '开' : '关'}
                      </button>
                    }
                  />
                  <Row
                    label="起草语气"
                    hint="影响项目助手怎么写稿（全局 AI 不受影响）"
                    control={
                      <Sel
                        value="same"
                        options={[
                          { value: 'same', label: '跟我平时一样' },
                          { value: 'short', label: '更短更利落' },
                          { value: 'long', label: '更详细' },
                        ]}
                        onChange={() => say('已保存')}
                      />
                    }
                  />
                </>
              )}

              {s.id === 'mem' && (
                <>
                  <Row
                    label="写入方式"
                    hint="推荐提案制：AI 建议，你确认"
                    control={
                      <Sel
                        value={settings?.product_prefs?.memory_write_mode ?? 'propose'}
                        options={[
                          { value: 'propose', label: '提案制（推荐）' },
                          { value: 'auto', label: '自动写入' },
                          { value: 'manual', label: '仅手动' },
                        ]}
                        onChange={(v) => void save({ product_prefs: { memory_write_mode: v as 'propose' | 'auto' | 'manual' } })}
                      />
                    }
                  />
                  <Row
                    label="路径画像"
                    hint="我想成为谁、发什么、红线"
                    control={
                      <Button variant="outlined" size="small" href="/path">
                        打开编辑
                      </Button>
                    }
                  />
                  <Row
                    label="判断记忆 / 公式"
                    hint="复盘「收下」后才生效"
                    control={
                      <Button variant="outlined" size="small" href="/review">
                        打开编辑
                      </Button>
                    }
                  />
                </>
              )}

              {s.id === 'priv' && (
                <>
                  <Row
                    label="素材默认隐私"
                    hint="「私密」不进生成、不外发"
                    control={
                      <Sel
                        value={settings?.product_prefs?.default_material_privacy ?? 'private'}
                        options={[
                          { value: 'private', label: '私密' },
                          { value: 'public', label: '可公开' },
                        ]}
                        onChange={(v) => void save({ product_prefs: { default_material_privacy: v as 'private' | 'public' } })}
                      />
                    }
                  />
                  <Row
                    label="导出全部数据"
                    hint="项目、素材、记忆、设置"
                    control={
                      <Button variant="outlined" size="small">
                        导出…
                      </Button>
                    }
                  />
                  <Row
                    label="删除账号"
                    hint="需你确认，不可撤销"
                    control={
                      <Button variant="outlined" color="error" size="small">
                        申请删除…
                      </Button>
                    }
                  />
                </>
              )}
          </div>
        ))}

        <div className="lumen-fill">设置已按「产品 / 全局 AI / 项目助手」分开 · 保存后生效</div>
      </div>
    </div>
  );
}
