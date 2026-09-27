import React, { useState, useEffect } from 'react';

function ChartModal({ open, onClose, data }) {
  const [chartPoints, setChartPoints] = useState(null);

  // Calculate chart points when data changes
  useEffect(() => {
    if (!open) return;
    const safeData = Array.isArray(data) ? data : [];
    const maxVal = safeData.length > 0 ? Math.max(...safeData.map(d => Math.max(d.total_price || 0, d.outbound_price || 0, d.return_price || 0))) || 1 : 1;
    const pts = safeData.map((d, i) => ({
      x: 30 + (i / Math.max(1, safeData.length - 1)) * 540,
      out: 190 - ((d.outbound_price || 0) / maxVal) * 150,
      ret: 190 - ((d.return_price || 0) / maxVal) * 150,
      tot: 190 - ((d.total_price || 0) / maxVal) * 150
    }));
    setChartPoints(pts);
  }, [open, data]);

  if (!open) return null;

  const safeData = Array.isArray(data) ? data : [];

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.85)',
        zIndex: 999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#0f172a',
          padding: 20,
          borderRadius: 8,
          maxWidth: 720,
          width: '92%',
          maxHeight: '82vh',
          overflow: 'auto'
        }}
        onClick={e => e.stopPropagation()}
      >
        <h3 style={{ color: '#f8fafc', marginBottom: 10, fontSize: 18 }}>Preisverlauf</h3>
        <svg
          width="100%"
          height="240"
          viewBox="0 0 600 240"
          style={{ background: '#1e293b', borderRadius: 6 }}
        >
          {chartPoints && chartPoints.length > 0 ? (
            <>
              <polyline key="hin" points={chartPoints.map(p => `${p.x},${p.out}`).join(' ')} fill="none" stroke="#38bdf8" strokeWidth="2"/>
              <polyline key="ret" points={chartPoints.map(p => `${p.x},${p.ret}`).join(' ')} fill="none" stroke="#f97316" strokeWidth="2"/>
              <polyline key="tot" points={chartPoints.map(p => `${p.x},${p.tot}`).join(' ')} fill="none" stroke="#10b981" strokeWidth="2"/>
              {/* X-Achse */}
              <text x="300" y="230" textAnchor="middle" fill="#94a3b8" fontSize="10">Datum →</text>
              {/* Y-Achse */}
              <text x="18" y="125" textAnchor="start" fill="#94a3b8" fontSize="10" transform="rotate(-90 18 125)">Preis (€) ↑</text>
              {/* Legende unterhalb */}
              <text x="580" y="235" textAnchor="end" fill="#38bdf8" fontSize="10">● Hin</text>
              <text x="580" y="225" textAnchor="end" fill="#f97316" fontSize="10">● Rück</text>
              <text x="580" y="215" textAnchor="end" fill="#10b981" fontSize="10">● Gesamt</text>
                {/* Dynamic Y-Scale from data */}
                {(() => {
                  const maxV = Math.max(...safeData.map(d => Math.max(d.total_price||0, d.outbound_price||0, d.return_price||0)));
                  const step = Math.ceil(maxV / 4 / 10) * 10 || 50;
                  const ticks = [0, step, step*2, step*3, maxV];
                  return ticks.map((v, i) => (
                    <text key={"y"+i} x="8" y={196 - (v/maxV)*150} fill="#64748b" fontSize="9">{v}</text>
                  ));
                })()}
                {/* Dynamic X labels from data dates */}
                {safeData.map((d, i) => (
                  <text key={"x"+i} x={30 + (i/(Math.max(1,safeData.length-1)))*540} y="245" textAnchor="middle" fill="#94a3b8" fontSize="9">{d.date?.split("-")[2]+"."||""}</text>
                ))}
                {/* Achsenlinien */}
                <line x1="30" y1="190" x2="570" y2="190" stroke="#334155" strokeWidth="1"/>
                <line x1="30" y1="40" x2="30" y2="190" stroke="#334155" strokeWidth="1"/>
            </>
          ) : safeData.length === 0 ? (
            <text x="300" y="130" textAnchor="middle" fill="#94a3b8" fontSize="14">Keine Daten</text>
          ) : null}
        </svg>
        <div style={{ marginTop: 8, color: '#e2e8f0', fontSize: 12 }}>
          {safeData.map(d => (
            <div key={d.date} style={{ marginBottom: 2 }}>{d.date}: Hin {d.outbound_price} € | Rück {d.return_price} € | Gesamt {d.total_price} €</div>
          ))}
        </div>
        <button
          onClick={e => { e.stopPropagation(); onClose(); }}
          style={{
            marginTop: 12,
            padding: '6px 14px',
            borderRadius: 6,
            border: 'none',
            background: '#475569',
            color: '#fff',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Schließen
        </button>
      </div>
    </div>
  );
}

export default ChartModal;
