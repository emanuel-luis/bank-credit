import React, { createContext, useContext, useState } from 'react';

type MockData = Record<number, any>;

interface MockApplicationContextProps {
  mockData: MockData;
  setMockData: (id: number, data: any) => void;
  getMockData: (id: number) => any;
}

const MockApplicationContext = createContext<MockApplicationContextProps | undefined>(undefined);

export const MockApplicationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Carrega do localStorage ao iniciar
  const [mockData, setMockDataState] = useState<MockData>(() => {
    const saved = localStorage.getItem('mockData');
    return saved ? JSON.parse(saved) : {};
  });

  const setMockData = (id: number, data: any) => {
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

export function useMockApplication() {
  const ctx = useContext(MockApplicationContext);
  if (!ctx) throw new Error('useMockApplication must be used within MockApplicationProvider');
  return ctx;
}