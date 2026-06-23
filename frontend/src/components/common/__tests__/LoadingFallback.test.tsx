import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LoadingFallback from '../LoadingFallback';
describe('LoadingFallback', () => {
  it('renders a circular progress', () => {
    const c = render(<LoadingFallback />).container;
    expect(c.querySelector('.MuiCircularProgress-root')).toBeTruthy();
  });
});
