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
  const [scrapeRunning, setScrapeRunning] = useState(false);
  const [futureInfo, setFutureInfo] = useState({});
  const [tripStart, setTripStart] = useState(new Date().toISOString().split('T')[0]);
  const [tripEnd, setTripEnd] = useState(new Date(Date.now() + 7*86400000).toISOString().split('T')[0]);
  const [startWeekdays, setStartWeekdays] = useState([4]);
  const [endWeekdays, setEndWeekdays] = useState([6]);
  const [maxDepToDest, setMaxDepToDest] = useState('18:00');
  const [minRetDep, setMinRetDep] = useState('10:00');
  const [maxTripDays, setMaxTripDays] = useState(5);
  const [startAirport, setStartAirport] = useState('');
  const [endAirport, setEndAirport] = useState('');
  const [turnarounds, setTurnarounds] = useState([]);
  const [airportNames, setAirportNames] = useState({});

  useEffect(() => {
    if (tab === 'trips' && tripStart && tripEnd && startWeekdays.length > 0 && endWeekdays.length > 0 && maxDepToDest && minRetDep && maxTripDays) {
      const params = new URLSearchParams({
        start: tripStart, end: tripEnd,
        start_days: startWeekdays.join(','), end_days: endWeekdays.join(','),
        max_dep_dest: maxDepToDest, min_ret_dep: minRetDep, max_trip_days: maxTripDays
      });
      if (startAirport) params.append("start_airport", startAirport);
      if (startAirport) params.append("end_airport", startAirport);
      params.append('max_trip_days', maxTripDays);
      fetch('/api/turnarounds?' + params.toString()).then(r => r.json()).then(data => setTurnarounds(data.turnarounds || data.results || [])).catch(() => setTurnarounds([]));
    }
  }, [tab, tripStart, tripEnd, startWeekdays, endWeekdays, maxDepToDest, minRetDep, startAirport, endAirport, maxTripDays]);

  useEffect(() => {
    if (tab === 'flights') loadFlights();
  }, [flightDate, tab]);
  useEffect(() => {
    if (tab === 'flights') loadFlights();
          fetch('/api/airports').then(r => r.json()).then(data => {
      const codes = Array.isArray(data) ? data.map(c => typeof c === 'string' ? c : c.code || c) : [];
      setList(codes);
      const nameMap = {};
      data.forEach(item => {
        const code = typeof item === 'string' ? item : item.code || item;
        const name = typeof item === 'string' ? '' : (item.name || item.name || '');
        if (code) nameMap[code] = name || code;
      });
      setAirportNames(nameMap);
    }).catch(() => setList([]));
    loadFlights();
    // Only call scrape-status as long as it is true (running)
    const check = () => {
      fetch('/api/flights/scrape-status').then(r => r.json()).then(d => {
        if (d.running) {
          setScrapeRunning(true);
          // keep checking while true
          setTimeout(check, 2000);
        } else {
          setScrapeRunning(false);
        }
      }).catch(() => setScrapeRunning(false));
    };
    check();
    // No fixed interval; only poll when running
    return () => {};
  }, []);

  const loadFlights = () => {
    const airport = document.getElementById('codeInput')?.value?.trim().toUpperCase() || '';
    let url = '/api/flights?';
    if (airport) url += 'airport=' + airport + '&';
    if (flightDate) url += 'date=' + flightDate;
    fetch(url).then(r => r.json()).then(data => { setFlights(data); fetch('/api/flights/future').then(r => r.json()).then(setFutureInfo).catch(() => setFutureInfo({})); }).catch(() => setFlights([]));
  };

  const checkScrape = () => {
    fetch('/api/flights/scrape-status').then(r => r.json()).then(d => {
      setScrapeRunning(!!d.running);
      if (d.running) {
        setTimeout(checkScrape, 2000);
      }
    }).catch(() => setScrapeRunning(false));
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
<h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Flight Schedule</h3>
              <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
                <input type='date' value={flightDate} onChange={e => { setFlightDate(e.target.value); loadFlights(); }} style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 15 }} />
                <button onClick={() => setFlightDate(new Date(new Date(flightDate).getTime() - 86400000).toISOString().split('T')[0])} style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#6366f1,#4f46e5)', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>◀ Vorheriger Tag</button>
                <button onClick={() => setFlightDate(new Date().toISOString().split('T')[0])} style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#f59e0b,#d97706)', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Heute</button>
                <button onClick={() => setFlightDate(new Date(new Date(flightDate).getTime() + 86400000).toISOString().split('T')[0])} style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#6366f1,#4f46e5)', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Nächster Tag ▶</button>
                <button onClick={async () => { await fetch('/api/flights/fetch-now', { method: 'POST' }); }} style={{ padding: '10px 18px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>Fetch Now</button>
                {scrapeRunning && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.35)' }}>
                    <div style={{ width: 16, height: 4, borderRadius: 2, background: 'linear-gradient(90deg,#10b981,#34d399,#10b981)', animation: 'pulse 1.5s infinite', backgroundSize: '200% 100%' }} />
                    <span style={{ fontSize: 12, color: '#34d399', fontWeight: 600 }}>Scraping läuft…</span>
                  </div>
                )}
              </div>
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
                        {futureInfo[airport] ? (futureInfo[airport].max_departure_day ? `Loaded until ${futureInfo[airport].max_departure_day}` : 'No future data') : '...'}
                      </span>
                    </div>
                    <div style={{ marginTop: 8, padding: 8 }}>{expanded[airport] ? (<div>
                      <div>
                        <strong style={{ color: '#4ade80', fontSize: 13 }}>Arrivals ({arr.length})</strong>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 6 }}>
                          <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>From</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Flight</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Departure</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Arrival</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Duration</th></tr></thead>
                          <tbody>
                            {arr.length === 0 && <tr><td colSpan="5" style={{ padding: '4px 8px', color: '#94a3b8' }}>No arrivals</td></tr>}
                            {arr.map(a => <tr key={a.id || a.destination_icao + a.departure_time} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                              <td style={{ padding: '4px 8px' }}>{a.from_icao ? (a.from_airport_name ? a.from_airport_name + ' (' + a.from_icao + ')' : (a.from_icao || a.airport_icao || airport)) : (a.airport_icao || airport)}</td>
                              <td style={{ padding: '4px 8px', fontWeight: 600 }}>{a.flight_number || '-'}</td>
                                                              <td style={{ padding: '4px 8px', color: '#38bdf8' }}>{a.departure_time ? (() => { const ts = a.departure_time; if (!ts) return '-'; const m = ts.match(/(\d{1,2}):(\d{2})/); if (m) return m[1] + ':' + m[2]; return ts.includes(':') ? ts.split(':').slice(0,2).join(':') : '-'; })() : '-'}</td>
                                                              <td style={{ padding: '4px 8px', color: '#4ade80' }}>{a.arrival_time ? (() => { const ts = a.arrival_time; if (!ts) return '-'; const m = ts.match(/(\d{1,2}):(\d{2})/); if (m) return m[1] + ':' + m[2]; return ts.includes(':') ? ts.split(':').slice(0,2).join(':') : '-'; })() : '-'}</td>
                              <td style={{ padding: '4px 8px', color: '#818cf8' }}>{a.duration_minutes ? a.duration_minutes + ' min' : '-'}</td>
                            </tr>)}
                          </tbody>
                        </table>
                      </div>
                      <div style={{ marginTop: 10 }}>
                        <strong style={{ color: '#38bdf8', fontSize: 13 }}>Departures ({dep.length})</strong>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 6 }}>
                          <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>To</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Flight</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Departure</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Arrival</th><th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8' }}>Duration</th></tr></thead>
                          <tbody>
                            {dep.length === 0 && <tr><td colSpan="5" style={{ padding: '4px 8px', color: '#94a3b8' }}>No departures</td></tr>}
                            {dep.map(d => <tr key={d.id || d.destination_icao + d.departure_time} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                              <td style={{ padding: '4px 8px' }}>{d.destination_name ? d.destination_name + ' (' + d.destination_icao + ')' : d.destination_icao}</td>
                              <td style={{ padding: '4px 8px', fontWeight: 600 }}>{d.flight_number || '-'}</td>
                              <td style={{ padding: '4px 8px', color: '#38bdf8' }}>{d.departure_time ? (() => { const ts = d.departure_time; if (!ts) return '-'; const m = ts.match(/(\d{1,2}):(\d{2})/); if (m) return m[1] + ':' + m[2]; return ts.includes(':') ? ts.split(':').slice(0,2).join(':') : '-'; })() : '-'}</td>
                              <td style={{ padding: '4px 8px', color: '#4ade80' }}>{d.arrival_time ? (() => { const ts = d.arrival_time; if (!ts) return '-'; const m = ts.match(/(\d{1,2}):(\d{2})/); if (m) return m[1] + ':' + m[2]; return ts.includes(':') ? ts.split(':').slice(0,2).join(':') : '-'; })() : '-'}</td>
                              <td style={{ padding: '4px 8px', color: '#818cf8' }}>{d.duration_minutes ? d.duration_minutes + ' min' : '-'}</td>
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
              <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Trip Turnaround Finder</h3>
              <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 18 }}>Find possible trip combinations based on date ranges and weekday preferences.</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 18, marginBottom: 18 }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Trip Start Date</label>
                  <input type="date" value={tripStart} onChange={e => setTripStart(e.target.value)} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 14 }} />
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Trip End Date</label>
                  <input type="date" value={tripEnd} onChange={e => setTripEnd(e.target.value)} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 14 }} />
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Start Weekdays</label>
                  <select multiple value={startWeekdays.map(String)} onChange={e => setStartWeekdays([...e.target.options].filter(o => o.selected).map(o => parseInt(o.value)))} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 13, height: 72 }}>
                    <option value="0">Monday</option>
                    <option value="1">Tuesday</option>
                    <option value="2">Wednesday</option>
                    <option value="3">Thursday</option>
                    <option value="4">Friday</option>
                    <option value="5">Saturday</option>
                    <option value="6">Sunday</option>
                  </select>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>End Weekdays</label>
                  <select multiple value={endWeekdays.map(String)} onChange={e => setEndWeekdays([...e.target.options].filter(o => o.selected).map(o => parseInt(o.value)))} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 13, height: 72 }}>
                    <option value="0">Monday</option>
                    <option value="1">Tuesday</option>
                    <option value="2">Wednesday</option>
                    <option value="3">Thursday</option>
                    <option value="4">Friday</option>
                    <option value="5">Saturday</option>
                    <option value="6">Sunday</option>
                  </select>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Latest Departure to Destination</label>
                  <input type="time" value={maxDepToDest} onChange={e => setMaxDepToDest(e.target.value)} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 14 }} />
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Airport (Start & End)</label>
                  <select value={startAirport} onChange={e => { setStartAirport(e.target.value); setEndAirport(e.target.value); }} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 13 }}>
                    <option value="">Select airport</option>
                    {list.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Earliest Return Departure</label>
                  <input type="time" value={minRetDep} onChange={e => setMinRetDep(e.target.value)} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 14 }} />
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: 6 }}>Max Trip Length (days)</label>
                  <input type="number" min={1} max={30} value={maxTripDays} onChange={e => setMaxTripDays(parseInt(e.target.value) || 1)} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 14 }} />
                </div>
              </div>
              <div style={{ marginBottom: 14, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <button onClick={async () => {
                  try {
                    const res = await fetch('/api/turnarounds?' + new URLSearchParams({
                      start: tripStart, end: tripEnd,
                      start_days: startWeekdays.join(','), end_days: endWeekdays.join(','),
                      max_dep_dest: maxDepToDest, min_ret_dep: minRetDep, max_trip_days: maxTripDays
                    }));
                    const data = await res.json();
                    setTurnarounds(data.turnarounds || data.results || []);
                  } catch (e) { setTurnarounds([]); }
                }} style={{ padding: '10px 20px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #38bdf8, #818cf8)', color: '#0f172a', fontWeight: 700, fontSize: 14, cursor: 'pointer', boxShadow: '0 4px 14px rgba(56,189,248,0.35)' }}>Calculate Turnarounds</button>
                <span style={{ fontSize: 12, color: '#94a3b8' }}>{turnarounds.length ? `${turnarounds.length} result${turnarounds.length > 1 ? 's' : ''}` : ''}</span>
              </div>
              {turnarounds.length > 0 && (() => {
                const groups = {};
                turnarounds.forEach(t => { const key = t.hinflug_ziel || t.destination || '-'; if (!groups[key]) groups[key] = []; groups[key].push(t); });
                const groupKeys = Object.keys(groups).sort();
                return (
                  <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, border: '1px solid rgba(255,255,255,0.08)' }}>
                    <h4 style={{ margin: '0 0 10px', fontSize: 15, fontWeight: 700, color: '#f8fafc' }}>Possible Turnarounds</h4>
                    {groupKeys.map(key => {
                      const group = groups[key];
                      const isOpen = !!expanded['trip_' + key];
                      return (
                        <div key={key} style={{ marginBottom: 10, border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, overflow: 'hidden' }}>
                          <button onClick={() => toggle('trip_' + key)} style={{ width: '100%', textAlign: 'left', padding: '10px 14px', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontWeight: 700, fontSize: 14, border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>{(group[0]?.hinflug_ziel_name || airportNames[key] ? (group[0]?.hinflug_ziel_name || airportNames[key] || key) + ' ' : '') + '(' + key + ')'}</span>
                            <span style={{ color: '#94a3b8', fontWeight: 500 }}>{isOpen ? '▲' : '▼'}</span>
                          </button>
                          {isOpen && (
                            <div style={{ padding: 8 }}>
                              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                                <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.12)' }}><th style={{ textAlign: 'left', padding: '6px 8px', color: '#94a3b8' }}>Outbound Flight</th><th style={{ textAlign: 'left', padding: '6px 8px', color: '#94a3b8' }}>Return Flight</th><th style={{ textAlign: 'left', padding: '6px 8px', color: '#94a3b8' }}>Trip Duration</th></tr></thead>
                                <tbody>
                                  {group.map((t, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                      <td style={{ padding: '6px 8px', color: '#f8fafc', fontWeight: 600 }}>
                                        {(t.hinflug_ziel_name || (t.hinflug_ziel || t.destination || '-') ? ((t.hinflug_ziel_name || (t.hinflug_ziel || t.destination || '-')) + ' (' + (t.hinflug_ziel || '-') + ')') : (t.hinflug_ziel || t.destination || '-') ) + ' → ' + (t.rueckflug_start_name || (t.rueckflug_start || t.start_airport || '-') ? ((t.rueckflug_start_name || (t.rueckflug_start || t.start_airport || '-')) + ' (' + (t.rueckflug_start || t.start_airport || '-') + ')') : (t.rueckflug_start || t.start_airport || '-') ) + ' (Hinflug ' + (t.hinflug_id || '-') + ') dep ' + (t.hinflug_abflug_zeit ? (t.hinflug_abflug_zeit.substring ? t.hinflug_abflug_zeit.substring(11,16) : t.hinflug_abflug_zeit) : '-')}
                                      </td>
                                      <td style={{ padding: '6px 8px', color: '#f8fafc', fontWeight: 600 }}>
                                        {(t.hinflug_ziel_name || (t.hinflug_ziel || t.destination || '-') ? ((t.hinflug_ziel_name || (t.hinflug_ziel || t.destination || '-')) + ' (' + (t.hinflug_ziel || '-') + ')') : (t.hinflug_ziel || t.destination || '-') ) + ' → ' + (t.rueckflug_start_name || (t.rueckflug_start || t.start_airport || '-') ? ((t.rueckflug_start_name || (t.rueckflug_start || t.start_airport || '-')) + ' (' + (t.rueckflug_start || t.start_airport || '-') + ')') : (t.rueckflug_start || t.start_airport || '-') ) + ' (Rückflug ' + (t.rueckflug_id || '-') + ') dep ' + (t.rueckflug_abflug_zeit ? (t.rueckflug_abflug_zeit.substring ? t.rueckflug_abflug_zeit.substring(11,16) : t.rueckflug_abflug_zeit) : '-')}
                                      </td>
                                      <td style={{ padding: '6px 8px', color: '#38bdf8' }}>{(t.dauer_tage !== undefined ? t.dauer_tage + 'd' : (t.days ? t.days + 'd' : '-'))}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            )}
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
              <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 16 }}>Configure max fetch months and scrape delay.</p>
              <form onSubmit={async (e) => {
                e.preventDefault();
                const body = { fetch_max_months: document.getElementById('fetchMaxMonths')?.value || 7 };
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
                  <label htmlFor="fetchMaxMonths" style={{ fontSize: 13, fontWeight: 600, color: '#f8fafc' }}>Max Fetch Months (1-12)</label>
                  <input id="fetchMaxMonths" type="number" min="1" max="12" defaultValue="1" placeholder="Months" style={{ padding: "10px 14px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.06)", color: "#f8fafc", fontSize: 15, width: '100%', maxWidth: 420, outline: "none" }} />
                  <span style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5, maxWidth: 360 }}>
                    The parameter <code>fetch_max_months</code> controls how many months ahead flight data is fetched. It is globally shared between all airports.
                  </span>
                </div>
                <button type="submit" style={{
                  marginTop: 8, padding: '10px 18px', borderRadius: 10, border: 'none',
                  background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                  color: '#0f172a', fontWeight: 700, fontSize: 15, cursor: 'pointer', alignSelf: 'flex-start'
                }}>Speichern</button>
              </form>
              <div style={{ marginTop: 20, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 16 }}>
                <h4 style={{ margin: '0 0 10px', fontSize: 15, fontWeight: 600, color: '#f8fafc' }}>Scrape Delay (ms)</h4>
                <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 10 }}>Delay between kayak requests in milliseconds.</p>
                <form onSubmit={async (e) => {
                  e.preventDefault();
                  const ms = parseInt(document.getElementById('delayMs')?.value || '500');
                  const res = await fetch('/api/settings/delay-ms', {
                    method: 'POST', headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({ delay_ms: ms })
                  });
                  if (!res.ok) alert('Failed to save delay');
                }} style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                  <input id="delayMs" type="number" min="0" max="5000" defaultValue="500" placeholder="ms" style={{ padding: '8px 12px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 14, width: 140 }} />
                  <button type="submit" style={{ padding: '8px 16px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #38bdf8, #818cf8)', color: '#0f172a', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}>Save</button>
                </form>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
