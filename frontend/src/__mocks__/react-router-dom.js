const React = require('react');

module.exports = {
  BrowserRouter: ({ children }) => 
    React.createElement('div', { 'data-testid': 'browser-router' }, children),
  MemoryRouter: ({ children, initialEntries }) => 
    React.createElement('div', { 
      'data-testid': 'memory-router', 
      'data-initial-entries': JSON.stringify(initialEntries || ['/']) 
    }, children),
  Routes: ({ children }) => 
    React.createElement('div', { 'data-testid': 'routes' }, children),
  Route: ({ children, path, element }) => 
    React.createElement('div', { 'data-testid': 'route', 'data-path': path }, element || children),
  useLocation: () => ({ 
    pathname: '/dashboard',
    search: '',
    hash: '',
    state: null,
    key: 'default'
  }),
  useNavigate: () => jest.fn(),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
  useHistory: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    go: jest.fn(),
    goBack: jest.fn(),
    goForward: jest.fn(),
  }),
  Link: ({ children, to, ...props }) => 
    React.createElement('a', { href: to, 'data-testid': 'router-link', ...props }, children),
  Navigate: ({ to }) => 
    React.createElement('div', { 'data-testid': 'navigate', 'data-to': to }),
  Outlet: () => React.createElement('div', { 'data-testid': 'router-outlet' }),
  createBrowserRouter: jest.fn(),
  RouterProvider: ({ router, children }) => 
    React.createElement('div', { 'data-testid': 'router-provider' }, children),
};