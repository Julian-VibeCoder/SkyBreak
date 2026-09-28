import React from 'react';

export default function Layout({ header, children }) {
  return (
    <div className="layout" style={{ display: 'flex', flexDirection: 'row', minHeight: '100vh', fontFamily: "'Inter', sans-serif", background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#f1f5f9' }}>
      <aside style={{ flexShrink: 0, width: 220, padding: '18px 14px', background: 'rgba(15,23,42,0.8)', borderRight: '1px solid rgba(255,255,255,0.08)' }}>
        {header}
      </aside>
      <main style={{ flex: 1, padding: '24px 20px', overflow: 'auto', maxWidth: '100%' }}>{children}</main>
    </div>
  );
}
