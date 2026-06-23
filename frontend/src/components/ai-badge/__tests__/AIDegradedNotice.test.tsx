import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AIDegradedNotice from '../AIDegradedNotice';

describe('AIDegradedNotice', () => {
  it('renders warning severity by default', () => {
    render(<AIDegradedNotice />);
    expect(screen.getByText('AI功能降级')).toBeInTheDocument();
  });
  it('renders error severity with custom message', () => {
    render(<AIDegradedNotice severity='error' message='Service unreachable' />);
    expect(screen.getByText('AI服务不可用')).toBeInTheDocument();
  });
});
