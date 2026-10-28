import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import CollapsibleSidebar from '../../frontend/src/components/CollapsibleSidebar';

describe('CollapsibleSidebar', () => {
  test('renders with toggle button for mobile', () => {
    render(<CollapsibleSidebar />);
    expect(screen.getByLabelText(/toggle sidebar/i)).toBeInTheDocument();
  });

  test('collapses sidebar on toggle click', () => {
    render(<CollapsibleSidebar />);
    const toggle = screen.getByLabelText(/toggle sidebar/i);
    fireEvent.click(toggle);
    expect(screen.getByRole('navigation')).toHaveClass('collapsed');
  });
});
