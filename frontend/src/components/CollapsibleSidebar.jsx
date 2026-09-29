import React, { useState, useEffect } from 'react';

export default function CollapsibleSidebar({ children, collapsed, onToggle }) {
  const [innerCollapsed, setInnerCollapsed] = useState(typeof window !== 'undefined' ? window.innerWidth < 1024 : false);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 1024 : false);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      if (mobile) setInnerCollapsed(collapsed === true);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [collapsed]);

  useEffect(() => { if (typeof collapsed === 'boolean') setInnerCollapsed(collapsed); }, [collapsed]);
  return (
    <aside className={innerCollapsed ? 'collapsed' : ''} style={{ position: 'relative' }}>
      <button
        aria-label="Toggle sidebar"
        onClick={() => { const next = !innerCollapsed; setInnerCollapsed(next); if (onToggle) onToggle(next); }}
        style={{
          position: 'absolute', top: 18, right: -22, zIndex: 50,
          width: 44, height: 44, borderRadius: '50%', border: 'none',
          background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
          color: '#0f172a', fontSize: 22, fontWeight: 800,
          boxShadow: '0 4px 15px rgba(56,189,248,0.35)', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.2s ease'
        }}
      >☰</button>
      <div style={{ display: innerCollapsed ? 'none' : 'block' }}>{children}</div>
    </aside>
  );
}
