import React, { useEffect, useState } from 'react';
import CollapsibleSidebar from './components/CollapsibleSidebar';
import Layout from './components/Layout';

const NAV = [
  { key: 'airports', label: 'Airports', icon: '✈️' },
  { key: 'flights', label: 'Flights', icon: '🛫' },
  { key: 'trips', label: 'Trips', icon: '🧳' },
  { key: 'costs', label: 'Costs', icon: '💰' },
  { key: 'settings', label: 'Settings', icon: '⚙️' },
];

export default function App() {
  const [tab, setTab] = useState('airports');
  const [code, setCode] = useState('');
  const [list, setList] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [flights, setFlights] = useState([]);
      const [expanded, setExpanded] = useState({});
    const toggle = (c) => setExpanded(e => ({...e, [c]: !e[c]}));
    const [flightDate, setFlightDate] = useState(new Date().toISOString().split('T')[0]);
  const [futureInfo, setFutureInfo] = useState({});
  const [apiKeyValue, setApiKeyValue] = useState(''); const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    if (tab === 'flights') loadFlights();
    fetch('/api/settings/check').then(r => r.json()).then(data => {
      const has = !!(data && data.has_key);
      setHasApiKey(has);
      if (has) setApiKeyValue('••••••••'); else setApiKeyValue('');
    }).catch(() => { setHasApiKey(false); setApiKeyValue(''); });
    fetch('/api/airports').then(r => r.json()).then(data => {
      const codes = Array.isArray(data) ? data.map(c => typeof c === 'string' ? c : c.code || c) : [];
      setList(codes);
    }).catch(() => setList([]));
    loadFlights();
  }, []);

  const loadFlights = () => {
    const airport = document.getElementById('codeInput')?.value?.trim().toUpperCase() || '';
    let url = '/api/flights?';
    if (airport) url += 'airport=' + airport + '&';
    if (flightDate) url += 'date=' + flightDate;
    fetch(url).then(r => r.json()).then(data => { setFlights(data); fetch('/api/flights/future').then(r => r.json()).then(setFutureInfo).catch(() => setFutureInfo({})); }).catch(() => setFlights([]));
  };

  const submit = async (e) => {
    e.preventDefault();
    const raw = code.trim().toUpperCase();
    if (!/^[A-Z0-9]{3}$/.test(raw)) { setFeedback('Ungültiger IATA-Code'); return; }
    const res = await fetch('/api/airports', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({code: raw}) });
    if (res.ok) {
      setFeedback('Gespeichert: ' + raw);
      setCode('');
      setList([...list, raw]);
      loadFlights();
    } else { setFeedback('Serverfehler'); }
  };

  const removeAirport = async (c) => {
    const res = await fetch('/api/airports/' + c, { method: 'DELETE' });
    if (res.ok) {
      setList(list.filter(x => x !== c));
      setFeedback('Entfernt: ' + c);
      loadFlights();
    } else { setFeedback('Fehler beim Entfernen'); }
  };

  return (
    <div style={{
      display: 'flex', minHeight: '100vh', fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#f1f5f9'
    }}>
      <CollapsibleSidebar><aside style={{
        width: 260, flexShrink: 0, background: 'rgba(15,23,42,0.85)',
        backdropFilter: 'blur(12px)', borderRight: '1px solid rgba(255,255,255,0.06)',
        padding: '28px 20px', display: 'flex', flexDirection: 'column', gap: 10,
        boxShadow: '4px 0 30px rgba(0,0,0,0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 28 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14,
            background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22, boxShadow: '0 4px 15px rgba(56,189,248,0.35)'
          }}>✈️</div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, letterSpacing: '-0.5px', fontWeight: 800, color: '#f8fafc' }}>SkyBreak</h1>
            <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 500 }}>Travel Dashboard</span>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {NAV.map(n => (
            <button key={n.key} onClick={() => setTab(n.key)} style={{
              textAlign: 'left', padding: '12px 14px', borderRadius: 12, border: 'none',
              background: tab === n.key ? 'rgba(56,189,248,0.15)' : 'transparent',
              color: tab === n.key ? '#38bdf8' : '#cbd5e1', fontWeight: 600, fontSize: 15,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12,
              transition: 'all 0.2s ease', boxShadow: tab === n.key ? 'inset 0 0 0 1px rgba(56,189,248,0.35)' : 'none'
            }}>
              <span style={{ fontSize: 18 }}>{n.icon}</span>
              {n.label}
            </button>
          ))}
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>
            SkyBreak v1.0 — Modern travel analytics
          </div>
        </div>
      </aside>
    </CollapsibleSidebar>

      <main style={{ flex: 1, padding: 36, overflow: 'auto' }}>
        <header style={{ marginBottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 28, fontWeight: 800, letterSpacing: '-0.8px' }}>
              {NAV.find(n => n.key === tab)?.label}
            </h2>
            <p style={{ margin: '6px 0 0', color: '#94a3b8', fontSize: 14 }}>
              {tab === 'airports' && 'Manage airport codes and view departures / arrivals.'}
              {tab === 'flights' && 'Browse flight schedules by airport and date.'}
              {tab === 'trips' && 'Plan trips and view itineraries.'}
              {tab === 'costs' && 'Track travel expenses and budget overview.'}
              {tab === 'settings' && 'Configure API key for flight data access.'}
            </p>
          </div>
        </header>

        <div style={{ display: 'grid', gap: 24, gridTemplateColumns: tab === 'airports' ? '1fr 1fr' : '1fr', alignItems: 'start' }}>
          {tab === 'airports' && (
            <>
              <section style={{
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
              }}>
                <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Add Airport</h3>
                <form onSubmit={submit} style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <input id="codeInput" value={code} maxLength={3} placeholder="LHR"
                    onChange={e => setCode(e.target.value.toUpperCase())}
                    style={{
                      flex: '1 1 120px', padding: '10px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)',
                      background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 15, outline: 'none'
                    }}/>
                  <button type="submit" style={{
                    padding: '10px 18px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                    color: '#0f172a', fontWeight: 700, fontSize: 15, cursor: 'pointer', boxShadow: '0 4px 14px rgba(56,189,248,0.35)'
                  }}>Speichern</button>
                </form>
                <p style={{ margin: '12px 0 0', minHeight: 24, color: feedback.includes('Gespeichert') ? '#4ade80' : (feedback.includes('Fehler') || feedback.includes('Ungültig')) ? '#f87171' : '#94a3b8', fontSize: 13, fontWeight: 500 }}>{feedback}</p>
              </section>

              <section style={{
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
              }}>
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
          )}

          {tab === 'flights' && (
            <section style={{
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
            }}>
              <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Flight Schedule</h3><div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}><input type='date' value={flightDate} onChange={e => { setFlightDate(e.target.value); loadFlights(); }} style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 15 }} /><button onClick={loadFlights} style={{ padding: '10px 18px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#38bdf8,#818cf8)', color: '#0f172a', fontWeight: 700, cursor: 'pointer' }}>Refresh</button><button onClick={async () => { await fetch('/api/flights/fetch-now', { method: 'POST' }); loadFlights(); }} style={{ padding: '10px 18px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>Fetch Now</button></div>
              {list.map(airport => {
                const arr = flights.filter(f => f.airport_icao === airport && f.direction === 'arrival');
                const dep = flights.filter(f => f.airport_icao === airport && f.direction === 'departure');
                return (
                  <div key={airport} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                      <button onClick={() => toggle(airport)} style={{ flex: 1, textAlign: 'left', padding: '12px 16px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontWeight: 700, fontSize: 16, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        {airport} <span style={{ color: '#94a3b8', fontWeight: 500 }}>✈️</span>
                      </button>
                      <span style={{ marginLeft: 10, fontSize: 12, color: '#38bdf8', fontWeight: 600 }}>
                        {futureInfo[airport] ? (futureInfo[airport].days_ahead !== null ? `+${futureInfo[airport].days_ahead} days ahead` : 'No future data') : '...'}
                      </span>
                    </div>
                    <div style={{ marginTop: 8, padding: 8 }}>{expanded[airport] ? (<div>
                      <div>
                        <strong style={{ color: '#4ade80', fontSize: 13 }}>Arrivals ({arr.length})</strong>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 6 }}>
                          <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>From</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Flight</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Time</th></tr></thead>
                          <tbody>
                            {arr.length === 0 && <tr><td colSpan="3" style={{ padding: '4px 8px', color: '#94a3b8' }}>No arrivals</td></tr>}
                            {arr.map(a => <tr key={a.id || a.destination_icao + a.departure_time} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                              <td style={{ padding: '4px 8px' }}>{a.destination_name ? a.destination_name + ' (' + a.destination_icao + ')' : a.destination_icao}</td>
                              <td style={{ padding: '4px 8px', fontWeight: 600 }}>{a.flight_number || '-'}</td>
                              <td style={{ padding: '4px 8px' }}>{a.departure_time ? (() => { const ts = a.departure_time; const dtLocal = new Date(ts.endsWith("Z") ? ts : ts + (ts.includes("+") || ts.includes("Z") ? "" : "+00:00")); return dtLocal.toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', timeZoneName: 'short' }) + ' (UTC→local)'; })() : '-'}</td>
                            </tr>)}
                          </tbody>
                        </table>
                      </div>
                      <div style={{ marginTop: 10 }}>
                        <strong style={{ color: '#38bdf8', fontSize: 13 }}>Departures ({dep.length})</strong>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 6 }}>
                          <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>To</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Flight</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Time</th></tr></thead>
                          <tbody>
                            {dep.length === 0 && <tr><td colSpan="3" style={{ padding: '4px 8px', color: '#94a3b8' }}>No departures</td></tr>}
                            {dep.map(d => <tr key={d.id || d.destination_icao + d.departure_time} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                              <td style={{ padding: '4px 8px' }}>{d.destination_name ? d.destination_name + ' (' + d.destination_icao + ')' : d.destination_icao}</td>
                              <td style={{ padding: '4px 8px', fontWeight: 600 }}>{d.flight_number || '-'}</td>
                              <td style={{ padding: '4px 8px' }}>{d.departure_time ? (() => { const ts = d.departure_time; const dtLocal = new Date(ts.endsWith("Z") ? ts : ts + (ts.includes("+") || ts.includes("Z") ? "" : "+00:00")); return dtLocal.toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', timeZoneName: 'short' }) + ' (UTC→local)'; })() : '-'}</td>
                            </tr>)}
                          </tbody>
                        </table>
                      </div>
                    </div>) : <span style={{ color: "#94a3b8", fontSize: 13 }}>Click to expand</span>}
                    </div>
                  </div>
                );
              })}
              {!list.length && <div style={{ color: '#94a3b8', fontSize: 14 }}>No airports saved yet.</div>}
            </section>
          )}

          {tab === 'trips' && (
            <section style={{
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
            }}>
              <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>My Trips</h3>
            </section>
          )}

          {tab === 'costs' && (
            <section style={{
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
            }}>
              <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Cost Overview</h3>
            </section>
          )}

          {tab === 'settings' && (
            <section style={{
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
            }}>
              <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>API Settings</h3>
              <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 16 }}>Store your RapidAPI key for aviation data access.</p>
              <form onSubmit={async (e) => {
                e.preventDefault();
                let raw = document.getElementById('apiKeyInput')?.value || ''; let key = (raw === '••••••••') ? null : raw;
                const body = { fetch_interval_minutes: document.getElementById('fetchInterval')?.value || 30, fetch_max_days: document.getElementById('fetchMaxDays')?.value || 7 };
                if (key !== null) body.api_key = key;
                const res = await fetch('/api/settings', {
                  method: 'POST',
                  headers: {'Content-Type':'application/json'},
                  body: JSON.stringify(body)
                });
                if (res.ok) {
                  // saved silently
                } else {
                  alert('Failed to save');
                }
              }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label htmlFor="apiKeyInput" style={{ fontSize: 13, fontWeight: 600, color: '#f8fafc' }}>API Key (RapidAPI)</label>
                  <input id="apiKeyInput" type="password" placeholder="RapidAPI Key" value={apiKeyValue}
                    onChange={e => { setApiKeyValue(e.target.value); setHasApiKey(e.target.value.trim().length > 0); }}
                    style={{
                      padding: '10px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)',
                      background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 15, outline: 'none', width: '100%', maxWidth: 420
                    }}/>
                  <span style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5, maxWidth: 360 }}>
                    API key for rapidapi.com → AeroDataBox API.
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label htmlFor="fetchInterval" style={{ fontSize: 13, fontWeight: 600, color: '#f8fafc' }}>Fetch Interval (minutes)</label>
                  <input id="fetchInterval" type="number" min="1" max="1440" defaultValue="30" placeholder="Minutes" style={{ padding: "10px 14px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.06)", color: "#f8fafc", fontSize: 15, width: '100%', maxWidth: 420, outline: "none" }} />
                  <span style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5, maxWidth: 360 }}>
                    How often flight data is fetched (minutes).
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label htmlFor="fetchMaxDays" style={{ fontSize: 13, fontWeight: 600, color: '#f8fafc' }}>Max Fetch Days (1-365)</label>
                  <input id="fetchMaxDays" type="number" min="1" max="365" defaultValue="7" placeholder="Max fetch days" style={{ padding: "10px 14px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.06)", color: "#f8fafc", fontSize: 15, width: '100%', maxWidth: 420, outline: "none" }} />
                  <span style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5, maxWidth: 360 }}>
                    The parameter <code>fetch_max_days</code> controls how many days ahead flight data is fetched. It is globally shared between all airports.
                  </span>
                </div>
                <button type="submit" style={{
                  marginTop: 8, padding: '10px 18px', borderRadius: 10, border: 'none',
                  background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                  color: '#0f172a', fontWeight: 700, fontSize: 15, cursor: 'pointer', alignSelf: 'flex-start'
                }}>Speichern</button>
              </form>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
