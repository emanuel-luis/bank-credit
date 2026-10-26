import { describe, expect, it } from 'vitest';
import { ALL_DOCUMENTS, DOCUMENT_LABELS, EVENT_LABELS, REQUIRED_DOCUMENTS, ROLE_LABELS, STATUS_LABELS } from './labels';

describe('labels', () => {
  it('has a non-empty pt-BR text for every code', () => {
    for (const map of [STATUS_LABELS, EVENT_LABELS, DOCUMENT_LABELS, ROLE_LABELS]) {
      for (const text of Object.values(map)) expect(text.length).toBeGreaterThan(0);
    }
    expect(STATUS_LABELS.IN_REVIEW).toBe('Em análise');
  });

  it('requires four documents and offers collateral as the optional fifth', () => {
    expect(REQUIRED_DOCUMENTS).toHaveLength(4);
    expect(ALL_DOCUMENTS).toEqual([...REQUIRED_DOCUMENTS, 'collateral']);
  });
});
