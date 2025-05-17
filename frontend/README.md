# Bank Credit Frontend

This is a React.js frontend for the Bank Credit API, following best practices for code structure, environment configuration, and test coverage.

## Features
- Authentication (register, login, JWT)
- Credit Requests management (create, list, update, route)
- Notifications (list, mark as read, delete)
- Process Graph visualization
- Environment-based API URL configuration
- Modern React structure with Context, Routing, and Service layers
- Unit tests with Jest and Testing Library

## Getting Started

### Prerequisites
- Node.js (v18+ recommended)
- npm (v9+ recommended)

### Installation
1. Navigate to the `frontend` folder:
   ```cmd
   cd frontend
   ```
2. Install dependencies:
   ```cmd
   npm install
   ```

### Environment Configuration
Create a `.env` file in the project root with the following content:
```env
VITE_API_URL=http://localhost:8000
```
Change the URL if your backend runs elsewhere.

### Running the App
To start the development server:
```cmd
npm run dev
```
The app will be available at [http://localhost:5173](http://localhost:5173) by default.

### Running Tests
To run all frontend tests:
```cmd
npm test
```

## Project Structure
```
frontend/
  src/
    api.js                # Axios instance with env-based baseURL
    services/             # API service modules (auth, creditRequests, notifications, graph)
    contexts/             # React Contexts (AuthContext)
    components/           # Shared UI components (Loader, PrivateRoute)
    pages/                # Main pages (Login, Register, Dashboard, etc)
    __tests__/            # Jest/Testing Library tests
  .env                    # API URL config
  jest.config.js          # Jest configuration
  .babelrc                # Babel config for Jest
```

## Connecting to the Backend
- The frontend expects the backend API to be running and accessible at the URL set in `.env` (`VITE_API_URL`).
- All endpoints are called relative to this base URL.
- JWT tokens are stored in `localStorage` and sent automatically in requests.

## Main Endpoints Used
- `/auth/register` - Register new user
- `/auth/token` - Login (returns JWT)
- `/auth/me` - Get current user
- `/requests` - Credit requests CRUD
- `/notifications` - Notifications CRUD
- `/graph` - Process graph data

## Good Practices Followed
- Environment variables for API URL
- Service layer for API calls
- Context for authentication state
- Private routes for protected pages
- Minimal, clear, and reusable components
- Test coverage for main pages/components
- ESLint for code quality

---

For any issues, check your backend is running and CORS is enabled for your frontend URL.
