/**
 * 今日待决：从项目列表挑出「需要你」的条目（与确认卡/下一步同源文案）。
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProjects } from '@/services/api/v2/projects';
import {
  needsMe,
  nextActionLabel,
} from '@/features/content/projectListModel';
import type { ContentProject } from '@/types/contracts/v2/content';

export default function TodayQueue() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<ContentProject[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    void listProjects()
      .then((list) => {
        if (!alive) return;
        const items = Array.isArray(list) ? list : (list as { items?: ContentProject[] })?.items || [];
        setRows(items.filter(needsMe).slice(0, 6));
      })
      .catch(() => {
        if (alive) setError('待决列表加载失败，可到「内容」里查看。');
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  if (loading) {
    return (
      <p className="pg-sub" aria-busy="true">
        正在读取待决列表…
      </p>
    );
  }
  if (error) {
    return (
      <p className="pg-sub" role="alert">
        {error}
      </p>
    );
  }
  if (rows.length === 0) {
    return (
      <p className="pg-sub">今天没有等你决定的事。可以「只记下来」或去内容里看看。</p>
    );
  }

  return (
    <section className="acard glass" aria-label="等你定" style={{ marginTop: 16 }}>
      <p className="kicker" style={{ marginTop: 0 }}>
        等你定 · {rows.length}
      </p>
      <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {rows.map((p) => (
          <li
            key={p.id}
            style={{
              display: 'flex',
              gap: 12,
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 0',
              borderTop: '1px solid rgba(23,28,38,0.06)',
            }}
          >
            <div style={{ minWidth: 0, flex: 1 }}>
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: '#191e26',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {p.title}
              </div>
              <div style={{ fontSize: 12, color: '#7e8898' }}>
                下一步：{nextActionLabel(p)}
              </div>
            </div>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => navigate(`/content/${p.id}`)}
            >
              去处理
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
