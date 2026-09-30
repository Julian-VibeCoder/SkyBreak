import React, { useState, useEffect } from 'react';

function ChartModal({ open, onClose, data }) {
  const [chartPoints, setChartPoints] = useState([]);
  const [dataPointsOpen, setDataPointsOpen] = useState(false);

  const parseDate = (s) => {
    if (!s) return null;
    const str = String(s).trim();
    if (str.includes('-')) {
      const [y, m, d] = str.split('-').map(Number);
      if (y && m && d) return new Date(y, m - 1, d).getTime();
    }
    if (str.includes('.')) {
      const parts = str.split('.');
      if (parts.length === 3) {
        const [d, m, y] = parts.map(Number);
        if (y && m && d) return new Date(y, m - 1, d).getTime();
      }
    }
    return null;
  };

  useEffect(() => {
    if (!open) return;
    const safeData = Array.isArray(data) ? data : [];
    const maxVal = safeData.length > 0
      ? Math.max(...safeData.map(d => Math.max(d.total_price || 0, d.outbound_price || 0, d.return_price || 0))) || 1
      : 1;
    const times = safeData.map(d => parseDate(d.date));
    const validTimes = times.filter(t => t != null);
    const minT = validTimes.length ? Math.min(...validTimes) : 0;
    const maxT = validTimes.length ? Math.max(...validTimes) : 0;
    const range = Math.max(1, maxT - minT);
    const pts = safeData.map((d, i) => {
      const t = times[i] != null ? times[i] : minT + (i / Math.max(1, safeData.length - 1)) * range;
      const nx = safeData.length <= 1 ? 310 : 60 + ((t - minT) / range) * 500;
      return {
        x: nx,
        out: 30 + 150 - ((d.outbound_price || 0) / maxVal) * 130,
        ret: 30 + 150 - ((d.return_price || 0) / maxVal) * 130,
        tot: 30 + 150 - ((d.total_price || 0) / maxVal) * 130,
        d
      };
    });
    setChartPoints(pts);
  }, [open, data]);

  if (!open) return null;
  const safeData = Array.isArray(data) ? data : [];
  const maxVal = safeData.length > 0
    ? Math.max(...safeData.map(d => Math.max(d.total_price || 0, d.outbound_price || 0, d.return_price || 0))) || 1
    : 1;
  const ticks = [0, Math.round(maxVal / 4), Math.round(maxVal / 2), Math.round(3 * maxVal / 4), maxVal];
  const isSingle = safeData.length === 1 || (safeData.length > 0 && chartPoints.length === 1);

  return (
    <div
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(2,6,23,0.88)', zIndex: 999,
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#0b1121', padding: 24,
          borderRadius: 16, maxWidth: 760, width: '94%',
          maxHeight: '88vh', overflow: 'auto',
          border: '1px solid rgba(148,163,184,0.15)',
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.7)'
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
          <h3 style={{ color: '#f1f5f9', margin: 0, fontSize: 18, fontWeight: 700, letterSpacing: 0.3 }}>Price Trend</h3>
          <button
            onClick={e => { e.stopPropagation(); onClose(); }}
            style={{ padding: '6px 12px', borderRadius: 8, border: 'none', background: '#334155', color: '#e2e8f0', fontWeight: 600, fontSize: 12, cursor: 'pointer' }}
          >
            Close
          </button>
        </div>

        <div style={{ background: '#111827', borderRadius: 12, padding: 16, border: '1px solid rgba(148,163,184,0.12)' }}>
          <svg
            width="100%"
            height={isSingle ? 180 : 260}
            viewBox={isSingle ? "0 0 600 180" : "0 0 600 260"}
            style={{ display: 'block' }}
          >
            <rect x="0" y="0" width="600" height={isSingle ? 180 : 260} fill="#0b1220" rx="8" />
            {ticks.map((t, i) => {
              const y = 30 + 150 - (t / maxVal) * 130;
              return (
                <g key={"grid"+i}>
                  <line x1="60" y1={y} x2="560" y2={y} stroke="#1e293b" strokeWidth="1" />
                  <text x="50" y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="10">{t}</text>
                </g>
              );
            })}
            <line x1="60" y1="30" x2="60" y2="180" stroke="#334155" strokeWidth="1.5" />
            <line x1="60" y1="180" x2="560" y2="180" stroke="#334155" strokeWidth="1.5" />
            <text x="310" y="205" textAnchor="middle" fill="#cbd5e1" fontSize="11" fontWeight="600">Date →</text>
            <text x="18" y="110" textAnchor="middle" fill="#cbd5e1" fontSize="11" fontWeight="600" transform="rotate(-90 18 110)">Price (€) ↑</text>

            {chartPoints.map((p, i) => (
              <g key={"pt"+i}>
                <circle cx={p.x} cy={p.out} r="4" fill="#38bdf8" stroke="#0f172a" strokeWidth="1.5" />
                <circle cx={p.x} cy={p.ret} r="4" fill="#f97316" stroke="#0f172a" strokeWidth="1.5" />
                <circle cx={p.x} cy={p.tot} r="5" fill="#10b981" stroke="#0f172a" strokeWidth="1.5" />
                {isSingle && (
                  <g>
                    <rect x={p.x - 55} y={p.tot - 45} width="110" height="34" rx="6" fill="#1e293b" stroke="#334155" strokeWidth="1" />
                    <text x={p.x} y={p.tot - 28} textAnchor="middle" fill="#f8fafc" fontSize="10" fontWeight="600">{p.d.date || '-'}</text>
                    <text x={p.x} y={p.tot - 14} textAnchor="middle" fill="#38bdf8" fontSize="9">Out {p.d.outbound_price ?? '—'} €</text>
                  </g>
                )}
              </g>
            ))}

            {chartPoints.length > 1 && (
              <>
                <polyline points={chartPoints.map(p => `${p.x},${p.out}`).join(' ')} fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                <polyline points={chartPoints.map(p => `${p.x},${p.ret}`).join(' ')} fill="none" stroke="#f97316" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                <polyline points={chartPoints.map(p => `${p.x},${p.tot}`).join(' ')} fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </>
            )}

            {isSingle && chartPoints.length === 1 && (
              <text x="300" y="245" textAnchor="middle" fill="#94a3b8" fontSize="10">Only one price entry available</text>
            )}

            {chartPoints.map((p, i) => (
              <text key={"x"+i} x={p.x} y={isSingle ? 165 : 245} textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="500">
                {p.d.date ? String(p.d.date).split("-")[2] + ".." + String(p.d.date).split("-")[1] : '-'}
              </text>
            ))}

            <g transform="translate(380, 10)">
              <rect x="0" y="-2" width="170" height="42" rx="6" fill="#0b1220" stroke="#334155" strokeWidth="1" />
              <line x1="10" y1="10" x2="28" y2="10" stroke="#38bdf8" strokeWidth="3" />
              <circle cx="19" cy="10" r="2.5" fill="#38bdf8" />
              <text x="36" y="14" fill="#e2e8f0" fontSize="10" fontWeight="600">Outbound</text>
              <line x1="10" y1="22" x2="28" y2="22" stroke="#f97316" strokeWidth="3" />
              <circle cx="19" cy="22" r="2.5" fill="#f97316" />
              <text x="36" y="26" fill="#e2e8f0" fontSize="10" fontWeight="600">Return</text>
              <line x1="10" y1="34" x2="28" y2="34" stroke="#10b981" strokeWidth="3" />
              <circle cx="19" cy="34" r="2.5" fill="#10b981" />
              <text x="36" y="38" fill="#e2e8f0" fontSize="10" fontWeight="600">Total</text>
            </g>
          </svg>
        </div>

        <div style={{ marginTop: 14, background: '#111827', padding: 12, borderRadius: 10, border: '1px solid rgba(148,163,184,0.1)' }}>
          <button onClick={() => setDataPointsOpen(o => !o)} style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}>
            <h4 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#e2e8f0' }}>Data Points</h4>
            <span style={{ color: '#94a3b8', fontSize: 14, fontWeight: 700 }}>{dataPointsOpen ? '−' : '+'}</span>
          </button>
          {dataPointsOpen && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 10 }}>
              {safeData.map((d, idx) => (
                <div key={d.date + '-' + idx} style={{ background: '#0b1220', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.08)' }}>
                  <div style={{ color: '#cbd5e1', fontWeight: 600, fontSize: 12 }}>{d.date ? String(d.date) : '—'}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                    Outbound <span style={{ color: '#38bdf8', fontWeight: 600 }}>{d.outbound_price ?? '—'} €</span> · Return <span style={{ color: '#f97316', fontWeight: 600 }}>{d.return_price ?? '—'} €</span> · Total <span style={{ color: '#10b981', fontWeight: 700 }}>{d.total_price ?? '—'} €</span>
                  </div>
                </div>
              ))}
              {safeData.length === 0 && (
                <div style={{ color: '#94a3b8', fontSize: 12, padding: 10 }}>No price history available for this trip.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChartModal;
