import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import { AuthContext } from '../contexts/AuthContext';

describe('Dashboard', () => {
  it('shows username and navigation', () => {
    render(
      <AuthContext.Provider value={{ user: { username: 'testuser' }, logout: jest.fn() }}>
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      </AuthContext.Provider>
    );
    expect(screen.getByText(/Bem-vindo, testuser/i)).toBeInTheDocument();
    expect(screen.getByText(/Solicitações de Crédito/i)).toBeInTheDocument();
    expect(screen.getByText(/Notificações/i)).toBeInTheDocument();
    expect(screen.getByText(/Fluxo de Processos/i)).toBeInTheDocument();
  });
});
