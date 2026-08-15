/**
 * Audit batch 5 (frontend scan e54a2643, bug-high round), batch C:
 * projectDraft storage key must be collision-free.
 *
 * Findings covered:
 * - The 'no-version' sentinel collided with a real version id literally
 *   named 'no-version' (both mapped to the same key).
 * - Raw interpolation made keys ambiguous when ids contain ':'
 *   (projectId 'a:b' + version 'c' vs projectId 'a' + version 'b:c').
 */
import { describe, expect, it } from 'vitest';
import { projectDraftKey, readProjectDraft } from '../projectDraft';

describe('projectDraftKey', () => {
  it('does not collide between a null base version and a literal id', () => {
    expect(projectDraftKey('p1', null)).not.toBe(projectDraftKey('p1', 'no-version'));
  });

  it('keeps ids containing colons unambiguous', () => {
    expect(projectDraftKey('a:b', 'c')).not.toBe(projectDraftKey('a', 'b:c'));
  });

  it('stays stable for the same project and base version', () => {
    expect(projectDraftKey('p1', 'v1')).toBe(projectDraftKey('p1', 'v1'));
    expect(projectDraftKey('p1', null)).toBe(projectDraftKey('p1', null));
  });
});

describe('readProjectDraft', () => {
  it('returns null for non-object JSON payloads', () => {
    // Audit e54a2643 medium: JSON.parse can yield null / primitives; the
    // reader must reject them explicitly instead of relying on a throw.
    localStorage.setItem(projectDraftKey('p1', 'v1'), 'null');
    expect(readProjectDraft('p1', 'v1')).toBeNull();

    localStorage.setItem(projectDraftKey('p1', 'v1'), '"text"');
    expect(readProjectDraft('p1', 'v1')).toBeNull();

    localStorage.setItem(projectDraftKey('p1', 'v1'), '42');
    expect(readProjectDraft('p1', 'v1')).toBeNull();
  });
});
