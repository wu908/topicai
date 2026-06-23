/**
 * Tests for RightPanel.
 *
 * Covers:
 * 1. Renders the section title based on the current route.
 * 2. Clicking the "发现新选题" CTA button navigates to /topics.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import RightPanel from '../RightPanel';

// Test helper: renders the current path so we can assert navigation happened.
const PathDisplay = () => {
  const location = useLocation();
  return <div data-testid="current-path">{location.pathname}</div>;
};

describe('RightPanel', () => {
  it('renders the 今日概览 section for the root route', () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <RightPanel />
      </MemoryRouter>
    );
    expect(screen.getByText('今日概览')).toBeInTheDocument();
  });

  it('clicking the "发现新选题" button navigates to /topics', () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <RightPanel />
        <PathDisplay />
      </MemoryRouter>
    );
    expect(screen.getByTestId('current-path')).toHaveTextContent('/');

    fireEvent.click(screen.getByRole('button', { name: /发现新选题/ }));

    expect(screen.getByTestId('current-path')).toHaveTextContent('/topics');
  });
});