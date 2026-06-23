import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Header from '../Header';

describe('Header', () => {
  it('renders without crashing', () => {
    const c = render(<Header />).container;
    expect(c.firstChild).toBeTruthy();
  });
});
