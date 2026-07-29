import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Chip, CircularProgress } from '@mui/material';
import { ArrowForward } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import { listProjectEvidence, listProjects } from '@/services/api/v2/projects';
import type { ContentProject } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import '../Operations.css';

type MaterialProject = ContentProject & { confirmedEvidenceCount: number };
const intentLabels = { solve: '解决', share: '分享', record: '记录' } as const;
// 历史内容的发布意图为空，只有回溯分类过才有可显示的意图。
const intentLabel = (project: MaterialProject) => {
  const intent = project.content_intent ?? project.retrospective_intent;
  return intent ? `${intentLabels[intent]}内容` : '未分类内容';
};

export default function MaterialsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<MaterialProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const list = await listProjects();
      const active = list.items.filter((project) => project.status !== 'settled');
      const evidence = await Promise.all(active.map((project) => listProjectEvidence(project.id)));
      setProjects(active.map((project, index) => ({
        ...project,
        confirmedEvidenceCount: evidence[index].filter((item) => item.confirmation_status === 'confirmed').length,
      })));
    } catch (err) {
      setError(extractErrorMessage(err, '素材准备情况加载失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <PageContainer title="素材" subtitle="按内容项目查看真实素材缺口，素材仍归属于正在推进的内容。">
      {loading ? <div className="operations-loading"><CircularProgress size={26} /></div> : (
        <>
          {error ? <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
          {projects.length ? <div className="operations-list">{projects.map((project) => (
            <article className="operations-row" key={project.id}>
              <div className="operations-row-header">
                <div><h2>{project.title}</h2><p className="operations-meta">{intentLabel(project)}</p></div>
                <Chip size="small" label={project.material_requirements.length ? `已确认 ${project.confirmedEvidenceCount} 条真实素材` : '素材需求待明确'} />
              </div>
              <p className="operations-row-copy">{project.audience_change || '先确认这条内容希望给读者带来的变化，AI 才能判断需要什么素材。'}</p>
              {project.material_requirements.length ? <ul className="operations-materials">{project.material_requirements.map((item) => <li key={item}>{item}</li>)}</ul> : null}
              <p className="operations-helper">真实素材数量仅用于提示准备情况，不代表每项需求已经逐一满足。</p>
              <div className="operations-row-actions"><Button endIcon={<ArrowForward />} onClick={() => navigate(`/content/${project.id}`)}>补充或确认素材</Button></div>
            </article>
          ))}</div> : (
            <section className="operations-empty"><h2>目前没有需要准备素材的内容</h2><p>创建内容项目并确认意图后，这里会汇总 AI 采访需要补齐的真实经历、观点和证据。</p><div className="operations-row-actions"><Button variant="contained" onClick={() => navigate('/content')}>开始一条内容</Button></div></section>
          )}
        </>
      )}
    </PageContainer>
  );
}
