/**
 * Tests for NotFoundPage — 404 fallback.
 *
 * Covers:
 * 1. Renders the 404 title and description
 * 2. Clicking "返回首页" navigates to /
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import NotFoundPage from '../NotFoundPage';

const navigateMock = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

function renderPage() {
  return render(
    <MemoryRouter>
      <NotFoundPage />
    </MemoryRouter>,
  );
}

describe('NotFoundPage', () => {
  it('renders the 404 title, subtitle, and description', () => {
    renderPage();
    expect(screen.getByText('404 — 页面走丢了')).toBeInTheDocument();
    expect(screen.getByText('页面不存在')).toBeInTheDocument();
    expect(screen.getByText(/你访问的页面不存在/)).toBeInTheDocument();
  });

  it('renders the "返回首页" action button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: '返回首页' })).toBeInTheDocument();
  });

  it('navigates to / when the action button is clicked', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '返回首页' }));
    expect(navigateMock).toHaveBeenCalledWith('/');
  });
});
