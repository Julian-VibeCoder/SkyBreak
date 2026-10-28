import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../../frontend/src/App';
import { fireEvent } from '@testing-library/react';

describe('Settings layout', () => {
  test('each setting gets its own labeled row with input and save button', () => {
    render(<App />);
    // Click settings tab
    fireEvent.click(screen.getByText('Settings'));
    // Every setting must have a visible label row
    expect(screen.getByLabelText(/API Key/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Fetch Interval/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Fetch Days Ahead/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Max Fetch Days/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Speichern/i })).toBeInTheDocument();
  });
});
