import React, { useState } from 'react';

export default function CollapsibleSidebar({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <aside className={collapsed ? 'collapsed' : ''}>
      <button aria-label="Toggle sidebar" onClick={() => setCollapsed(c => !c)}>☰</button>
      <div style={{ display: collapsed ? 'none' : 'block' }}>{children}</div>
    </aside>
  );
}
