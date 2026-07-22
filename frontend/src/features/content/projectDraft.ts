export interface ProjectDraft {
  projectId: string;
  baseVersionId: string | null;
  title: string;
  bodyText: string;
  savedAt: string;
}

const DRAFT_PREFIX = 'topicai:content-draft:v1';

export function projectDraftKey(projectId: string, baseVersionId: string | null) {
  return `${DRAFT_PREFIX}:${projectId}:${baseVersionId ?? 'no-version'}`;
}

export function readProjectDraft(projectId: string, baseVersionId: string | null) {
  try {
    const raw = localStorage.getItem(projectDraftKey(projectId, baseVersionId));
    if (!raw) return null;
    const draft = JSON.parse(raw) as Partial<ProjectDraft>;
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
