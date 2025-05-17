import React from 'react';
import { render, screen } from '@testing-library/react';
import GraphPage from '../pages/GraphPage';

jest.mock('../services/graph', () => ({
  getProcessGraph: () => Promise.resolve({ data: { nodes: [{ id: 1, name: 'Proc', next_process_id: null, sectors: ['A'] }], edges: [] } }),
  visualizeProcessGraph: () => Promise.resolve({ data: { nodes: [{ id: 1, label: 'Proc' }], edges: [] } }),
}));

describe('GraphPage', () => {
  it('renders process graph', async () => {
    render(<GraphPage />);
    expect(await screen.findByText(/Fluxo de Processos/i)).toBeInTheDocument();
    expect(await screen.findByText(/Proc/i)).toBeInTheDocument();
  });
});
