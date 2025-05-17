import React from 'react';
import { render, screen } from '@testing-library/react';
import CreditRequestsPage from '../pages/CreditRequestsPage';

jest.mock('../services/creditRequests', () => ({
  getCreditRequests: () => Promise.resolve({ data: [
    { id: 1, amount: 1000, status: 'PENDING' }
  ] }),
  createCreditRequest: jest.fn(),
  getRequestHistory: () => Promise.resolve({ data: [] }),
  updateCreditRequestStatus: jest.fn(),
  routeRequestToNext: jest.fn(),
}));

describe('CreditRequestsPage', () => {
  it('renders credit requests', async () => {
    render(<CreditRequestsPage />);
    expect(await screen.findByText(/Minhas Solicitações de Crédito/i)).toBeInTheDocument();
    expect(await screen.findByText(/PENDING/i)).toBeInTheDocument();
  });
});
