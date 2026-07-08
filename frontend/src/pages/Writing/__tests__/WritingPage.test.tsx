import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import WritingPage from '../WritingPage';

describe('WritingPage', () => {
  it('renders as an alias for IdeaBoosterPage', () => {
    // WritingPage just delegates to IdeaBoosterPage
    const { container } = render(<WritingPage />);
    expect(container.firstChild).toBeTruthy();
  });
});
