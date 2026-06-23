import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Modal from '../Modal';

describe('Modal', () => {
  it('renders open modal with title and children', () => {
    render(<Modal open={true} onClose={vi.fn()} title="Test Modal"><div data-testid="modal-child">Content</div></Modal>);
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByTestId('modal-child')).toBeInTheDocument();
  });
  it('renders footer button when footer is provided', () => {
    render(<Modal open={true} onClose={vi.fn()} title="With Footer" footer={<button data-testid="footer-btn">OK</button>}><div>Body</div></Modal>);
    expect(screen.getByTestId('footer-btn')).toBeInTheDocument();
  });
  it('does not render when closed', () => {
    render(<Modal open={false} onClose={vi.fn()} title="Hidden"><div>X</div></Modal>);
    expect(screen.queryByText('Hidden')).toBeNull();
  });
  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn();
    render(<Modal open={true} onClose={onClose} title="Closable"><div>Body</div></Modal>);
    screen.getByLabelText('关闭').click();
    expect(onClose).toHaveBeenCalled();
  });
});
