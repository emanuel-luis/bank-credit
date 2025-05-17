// eslint-disable-next-line
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['@testing-library/jest-dom'],
  moduleFileExtensions: ['js', 'jsx'],
  testMatch: ['**/__tests__/**/*.test.jsx'],
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
};
