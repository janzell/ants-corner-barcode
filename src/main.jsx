import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error?.message || 'Unexpected application error.'
    };
  }

  componentDidCatch(error) {
    console.error('App crash caught by ErrorBoundary:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ maxWidth: 620, margin: '60px auto', padding: 24, background: '#fff', borderRadius: 10, fontFamily: 'Inter, sans-serif' }}>
          <h2 style={{ marginTop: 0 }}>Something went wrong</h2>
          <p>The app hit a runtime error. Please refresh the page.</p>
          <p style={{ color: '#b00' }}>{this.state.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
