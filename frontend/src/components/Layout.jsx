import React from 'react';

export default function Layout({ header, children }) {
  return (
    <div className="layout" style={{ display: 'flex', minHeight: '100vh', fontFamily: "'Inter', sans-serif", background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#f1f5f9' }}>
      <header>{header}</header>
      <main style={{ flex: 1, padding: '36px', overflow: 'auto' }}>{children}</main>
    </div>
  );
}
