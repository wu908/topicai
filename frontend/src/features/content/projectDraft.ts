export interface ProjectDraft {
  projectId: string;
  baseVersionId: string | null;
  title: string;
  bodyText: string;
  savedAt: string;
}

const DRAFT_PREFIX = 'topicai:content-draft:v1';

// 审计 e54a2643 batch C：键必须无碰撞。id 里出现 ':' 时裸拼接会产生歧义键
// （'a:b'+'c' 与 'a'+'b:c'），null 哨兵也会和真实 id 'no-version' 撞车。
export function projectDraftKey(projectId: string, baseVersionId: string | null) {
  const versionPart = baseVersionId === null
    ? 'n'
    : `v${encodeURIComponent(baseVersionId)}`;
  return `${DRAFT_PREFIX}:${encodeURIComponent(projectId)}:${versionPart}`;
}

export function readProjectDraft(projectId: string, baseVersionId: string | null) {
  try {
    const raw = localStorage.getItem(projectDraftKey(projectId, baseVersionId));
    if (!raw) return null;
    // JSON.parse can legitimately yield null / primitives — reject them
    // explicitly instead of relying on a property-access throw.
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== 'object' || parsed === null) return null;
    const draft = parsed as Partial<ProjectDraft>;
    if (
      draft.projectId !== projectId
      || draft.baseVersionId !== baseVersionId
      || typeof draft.title !== 'string'
      || typeof draft.bodyText !== 'string'
      || typeof draft.savedAt !== 'string'
    ) {
      return null;
    }
    return draft as ProjectDraft;
  } catch {
    return null;
  }
}

export function writeProjectDraft(draft: ProjectDraft) {
  try {
    localStorage.setItem(projectDraftKey(draft.projectId, draft.baseVersionId), JSON.stringify(draft));
  } catch {
    // Private browsing and storage quotas must not block editing.
  }
}

export function removeProjectDraft(projectId: string, baseVersionId: string | null) {
  try {
    localStorage.removeItem(projectDraftKey(projectId, baseVersionId));
  } catch {
    // Storage cleanup is best effort.
  }
}
