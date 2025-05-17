import React from 'react';
import { render, screen } from '@testing-library/react';
import NotificationsPage from '../pages/NotificationsPage';

jest.mock('../services/notifications', () => ({
  getNotifications: () => Promise.resolve({ data: [
    { id: 1, subject: 'Test', message: 'Msg', read: false, created_at: new Date().toISOString() }
  ] }),
  markNotificationAsRead: jest.fn(),
  markAllNotificationsAsRead: jest.fn(),
  deleteNotification: jest.fn(),
}));

describe('NotificationsPage', () => {
  it('renders notifications', async () => {
    render(<NotificationsPage />);
    expect(await screen.findByText(/Test/i)).toBeInTheDocument();
    expect(screen.getByText(/Msg/i)).toBeInTheDocument();
  });
});
