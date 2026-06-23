import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import AppLayout from '../AppLayout';

describe('AppLayout', () => {
  it('renders children', () => {
    render(<MemoryRouter><AppLayout><div data-testid="kid">hi</div></AppLayout></MemoryRouter>);
    expect(screen.getByTestId('kid')).toBeInTheDocument();
  });
});