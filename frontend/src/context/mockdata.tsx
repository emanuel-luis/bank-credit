import React, { createContext, useContext, useState } from 'react';
import type { StoredForm } from '../types';

type MockData = Record<number, StoredForm>;

interface MockApplicationContextProps {
  mockData: MockData;
  setMockData: (id: number, data: StoredForm) => void;
  getMockData: (id: number) => StoredForm | undefined;
}

const MockApplicationContext = createContext<MockApplicationContextProps | undefined>(undefined);

export const MockApplicationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Carrega do localStorage ao iniciar
  const [mockData, setMockDataState] = useState<MockData>(() => {
    const saved = localStorage.getItem('mockData');
    return saved ? JSON.parse(saved) : {};
  });

  const setMockData = (id: number, data: StoredForm) => {
    setMockDataState(prev => {
      const updated = { ...prev, [id]: data };
      localStorage.setItem('mockData', JSON.stringify(updated)); // Salva no localStorage
      return updated;
    });
  };

  const getMockData = (id: number) => mockData[id];

  return (
    <MockApplicationContext.Provider value={{ mockData, setMockData, getMockData }}>
      {children}
    </MockApplicationContext.Provider>
  );
};

// Hook next to its provider on purpose; the whole context is replaced in phase 4.
// eslint-disable-next-line react-refresh/only-export-components
export function useMockApplication() {
  const ctx = useContext(MockApplicationContext);
  if (!ctx) throw new Error('useMockApplication must be used within MockApplicationProvider');
  return ctx;
}