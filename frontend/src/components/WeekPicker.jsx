import React from 'react';

export default function WeekPicker({ date, onChange }) {
  const d = new Date(date || new Date());
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d); monday.setDate(diff);
  const days = [];
  for (let i = 0; i < 7; i++) {
    const tmp = new Date(monday); tmp.setDate(monday.getDate() + i);
    days.push(tmp.toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'short' }));
  }
  return (
    <div className="week-picker" style={{ padding: '10px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', fontSize: 13, fontWeight: 600, color: '#e2e8f0', display: 'flex', gap: 10, alignItems: 'center' }}>
      <strong>Woche (Mo-So):</strong> {days.join(' | ')}
      <button onClick={() => { const prev = new Date(d); prev.setDate(d.getDate()-7); onChange && onChange(prev); }} style={{ padding: '4px 8px', borderRadius: 6, border: 'none', background: '#38bdf8', color: '#0f172a', cursor: 'pointer' }}>◀</button>
      <button onClick={() => { const next = new Date(d); next.setDate(d.getDate()+7); onChange && onChange(next); }} style={{ padding: '4px 8px', borderRadius: 6, border: 'none', background: '#38bdf8', color: '#0f172a', cursor: 'pointer' }}>▶</button>
    </div>
  );
}
