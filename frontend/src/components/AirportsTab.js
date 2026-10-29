import React, { useState } from 'react';

const sectionStyle = {
  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
};

// Add / list / delete saved airports. `list` and `setList` are owned by App so
// the Flights and Trips tabs share the same airport list.
export default function AirportsTab({ list, setList }) {
  const [code, setCode] = useState('');
  const [feedback, setFeedback] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    const raw = code.trim().toUpperCase();
    if (!/^[A-Z0-9]{3}$/.test(raw)) { setFeedback('Invalid IATA code'); return; }
    const res = await fetch('/api/airports', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: raw })
    });
    if (res.ok) {
      setFeedback('Gespeichert: ' + raw);
      setCode('');
      setList([...list, raw]);
    } else {
      setFeedback('Serverfehler');
    }
  };

  const removeAirport = async (c) => {
    const res = await fetch('/api/airports/' + c, { method: 'DELETE' });
    if (res.ok) {
      setList(list.filter(x => x !== c));
      setFeedback('Entfernt: ' + c);
    } else {
      setFeedback('Fehler beim Entfernen');
    }
  };

  return (
    <>
      <section style={sectionStyle}>
        <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Add Airport</h3>
        <form onSubmit={submit} style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input id="codeInput" value={code} maxLength={3} placeholder="LHR"
            onChange={e => setCode(e.target.value.toUpperCase())}
            style={{
              flex: '1 1 120px', padding: '10px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)',
              background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 15, outline: 'none'
            }} />
          <button type="submit" style={{
            padding: '10px 18px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
            color: '#0f172a', fontWeight: 700, fontSize: 15, cursor: 'pointer', boxShadow: '0 4px 14px rgba(56,189,248,0.35)'
          }}>Save</button>
        </form>
        <p style={{ margin: '12px 0 0', minHeight: 24, color: feedback.includes('Saved') ? '#4ade80' : (feedback.includes('Serverfehler') || feedback.includes('Invalid') || feedback.includes('Fehler')) ? '#f87171' : '#94a3b8', fontSize: 13, fontWeight: 500 }}>{feedback}</p>
      </section>

      <section style={sectionStyle}>
        <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Saved Airports</h3>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {list.map(c => (
            <li key={c} style={{
              background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 10, padding: '8px 14px', display: 'flex', alignItems: 'center', gap: 10
            }}>
              <span style={{ fontWeight: 700, color: '#38bdf8', letterSpacing: '0.5px' }}>{c}</span>
              <button onClick={() => removeAirport(c)} style={{
                background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: 6, color: '#f87171',
                fontSize: 14, cursor: 'pointer', padding: '2px 6px', lineHeight: 1
              }} title="Entfernen">×</button>
            </li>
          ))}
          {!list.length && <li style={{ color: '#94a3b8', fontSize: 14 }}>No airports saved yet.</li>}
        </ul>
      </section>
    </>
  );
}
