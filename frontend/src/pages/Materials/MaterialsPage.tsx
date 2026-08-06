import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
  Stack,
  TextField,
} from '@mui/material';
import { Add, DeleteOutline, LinkOutlined, UploadFile } from '@mui/icons-material';
import PageContainer from '@/components/layout/PageContainer';
import {
  addMaterialUsage,
  createMaterial,
  deleteMaterial,
  listMaterials,
  listProjects,
} from '@/services/api/v2/projects';
import type { ContentProject, Material } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import '../Operations.css';

const privacyLabels = { public: '公开', private: '私密', sensitive: '敏感' } as const;
const kindLabels = { text: '文字', link: '链接', image: '图片', document: '文档' } as const;
const key = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;

async function fileBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [projects, setProjects] = useState<ContentProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [kind, setKind] = useState<Material['kind']>('text');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [privacy, setPrivacy] = useState<Material['privacy_level']>('private');
  const [projectId, setProjectId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [reuseProject, setReuseProject] = useState<Record<string, string>>({});
  const [deleteImpact, setDeleteImpact] = useState<Record<string, string[]>>({});

  const load = useCallback(async () => {
    setError(null);
    try {
      const [materialList, projectList] = await Promise.all([listMaterials(), listProjects()]);
      setMaterials(materialList.items);
      setProjects(projectList.items.filter((item) => item.status !== 'settled'));
    } catch (err) {
      setError(extractErrorMessage(err, '素材加载失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await createMaterial({
        kind,
        title: title.trim(),
        ...(kind === 'text' || kind === 'link' ? { content: content.trim() } : {
          content_base64: await fileBase64(file as File),
          mime_type: file?.type || 'application/octet-stream',
        }),
        privacy_level: privacy,
        project_id: projectId || undefined,
        idempotency_key: key('material'),
      });
      setTitle('');
      setContent('');
      setFile(null);
      setProjectId('');
      setShowCreate(false);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, '素材保存失败'));
    } finally {
      setBusy(false);
    }
  };

  const link = async (materialId: string) => {
    const selected = reuseProject[materialId];
    if (!selected) return;
    setBusy(true);
    try {
      await addMaterialUsage(materialId, {
        project_id: selected,
        idempotency_key: key(`material-usage-${materialId}`),
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, '素材关联失败'));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (material: Material, confirmed = false) => {
    setBusy(true);
    try {
      await deleteMaterial(material.id, confirmed);
      setDeleteImpact((current) => ({ ...current, [material.id]: [] }));
      await load();
    } catch (err) {
      const response = (err as { response?: { data?: { meta?: { details?: { projects?: Array<{ title: string }> } } } } }).response;
      const affected = response?.data?.meta?.details?.projects?.map((item) => item.title) || [];
      if (affected.length) setDeleteImpact((current) => ({ ...current, [material.id]: affected }));
      else setError(extractErrorMessage(err, '素材删除失败'));
    } finally {
      setBusy(false);
    }
  };

  const needsFile = kind === 'image' || kind === 'document';
  const canSave = Boolean(title.trim() && (needsFile ? file : content.trim()));

  return (
    <PageContainer title="素材" subtitle="保存可复用的真实经历、链接、图片和文档，并查看它们正在支持哪些内容。">
      <div className="operations-row-actions">
        <Button variant="contained" startIcon={<Add />} onClick={() => setShowCreate((value) => !value)}>
          添加素材
        </Button>
      </div>
      {showCreate ? (
        <section className="operations-row">
          <Stack spacing={2}>
            <TextField select label="素材类型" value={kind} onChange={(event) => setKind(event.target.value as Material['kind'])}>
              {Object.entries(kindLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
            </TextField>
            <TextField label="素材标题" value={title} onChange={(event) => setTitle(event.target.value)} required />
            {needsFile ? (
              <Button component="label" variant="outlined" startIcon={<UploadFile />}>
                {file?.name || '选择文件'}
                <input hidden type="file" accept={kind === 'image' ? 'image/*' : undefined} onChange={(event) => setFile(event.target.files?.[0] || null)} />
              </Button>
            ) : (
              <TextField label="素材内容" value={content} onChange={(event) => setContent(event.target.value)} type={kind === 'link' ? 'url' : 'text'} multiline={kind === 'text'} minRows={kind === 'text' ? 4 : undefined} required />
            )}
            <TextField select label="隐私级别" value={privacy} onChange={(event) => setPrivacy(event.target.value as Material['privacy_level'])}>
              {Object.entries(privacyLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
            </TextField>
            <TextField select label="关联项目" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <MenuItem value="">暂不关联</MenuItem>
              {projects.map((project) => <MenuItem key={project.id} value={project.id}>{project.title}</MenuItem>)}
            </TextField>
            <div className="operations-row-actions">
              <Button variant="contained" disabled={busy || !canSave} onClick={() => void save()}>保存素材</Button>
              <Button color="inherit" disabled={busy} onClick={() => setShowCreate(false)}>取消</Button>
            </div>
          </Stack>
        </section>
      ) : null}
      {error ? <Alert severity="error" action={<Button onClick={() => void load()}>重试</Button>}>{error}</Alert> : null}
      {loading ? <div className="operations-loading"><CircularProgress size={26} /></div> : materials.length ? (
        <div className="operations-list">
          {materials.map((material) => (
            <article className="operations-row" key={material.id}>
              <div className="operations-row-header">
                <div><h2>{material.title}</h2><p className="operations-meta">{kindLabels[material.kind]} · {Math.max(1, Math.ceil(material.size / 1024))} KB</p></div>
                <Chip size="small" label={privacyLabels[material.privacy_level]} color={material.privacy_level === 'sensitive' ? 'warning' : 'default'} />
              </div>
              {material.content ? <p className="operations-row-copy">{material.content}</p> : null}
              <p className="operations-helper">
                {material.usages.length ? `正在用于：${material.usages.map((usage) => usage.project_title).join('、')}` : '尚未关联内容项目'}
              </p>
              {deleteImpact[material.id]?.length ? (
                <Alert severity="warning" action={<Button color="inherit" disabled={busy} onClick={() => void remove(material, true)}>保留引用快照并删除</Button>}>
                  将影响：{deleteImpact[material.id].join('、')}
                </Alert>
              ) : null}
              <div className="operations-row-actions">
                <TextField
                  select
                  size="small"
                  label="复用到项目"
                  value={reuseProject[material.id] || ''}
                  onChange={(event) => setReuseProject((current) => ({ ...current, [material.id]: event.target.value }))}
                  sx={{ minWidth: 180 }}
                >
                  <MenuItem value="">选择项目</MenuItem>
                  {projects.filter((project) => !material.usages.some((usage) => usage.project_id === project.id)).map((project) => <MenuItem key={project.id} value={project.id}>{project.title}</MenuItem>)}
                </TextField>
                <Button startIcon={<LinkOutlined />} disabled={busy || !reuseProject[material.id]} onClick={() => void link(material.id)}>关联</Button>
                <Button color="error" startIcon={<DeleteOutline />} disabled={busy} onClick={() => void remove(material)}>删除</Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <section className="operations-empty"><h2>还没有素材</h2><p>先保存一条真实经历、链接或图片，后续项目可以直接复用。</p></section>
      )}
    </PageContainer>
  );
}
