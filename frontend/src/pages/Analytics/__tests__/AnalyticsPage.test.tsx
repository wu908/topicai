import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AnalyticsPage from '../AnalyticsPage';

describe('AnalyticsPage', () => {
  it('renders the page title and empty state', () => {
    render(<AnalyticsPage />);
    expect(screen.getByText('数据分析')).toBeInTheDocument();
    expect(screen.getByText('数据分析面板')).toBeInTheDocument();
  });
});
