import React, { useState, useEffect } from 'react';
import { formatTime } from '../utils/format';

const sectionStyle = {
  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
};

const thStyle = { textAlign: 'left', padding: '4px 8px', color: '#94a3b8' };
const tdStyle = { padding: '4px 8px' };

function FlightTable({ title, rows, empty, firstCol, firstLabel }) {
  return (
    <div>
      <strong style={{ color: title.includes('Arrival') ? '#4ade80' : '#38bdf8', fontSize: 13 }}>{title}</strong>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 6 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <th style={thStyle}>{firstLabel}</th>
            <th style={thStyle}>Flight</th>
            <th style={thStyle}>Departure</th>
            <th style={thStyle}>Arrival</th>
            <th style={thStyle}>Duration</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && <tr><td colSpan="5" style={{ ...tdStyle, color: '#94a3b8' }}>{empty}</td></tr>}
          {rows.map(f => (
            <tr key={f.id || f.destination_icao + f.departure_time} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={tdStyle}>{firstCol(f)}</td>
              <td style={{ ...tdStyle, fontWeight: 600 }}>{f.flight_number || '-'}</td>
              <td style={{ ...tdStyle, color: '#38bdf8' }}>{formatTime(f.departure_time)}</td>
              <td style={{ ...tdStyle, color: '#4ade80' }}>{formatTime(f.arrival_time)}</td>
              <td style={{ ...tdStyle, color: '#818cf8' }}>{f.duration_minutes ? f.duration_minutes + ' min' : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Flight schedule for a saved airport, per date. Owns its own date/flight data.
export default function FlightsTab({ list, onFetchNow, fetchRunning }) {
  const [flightDate, setFlightDate] = useState(new Date().toISOString().split('T')[0]);
  const [flights, setFlights] = useState([]);
  const [futureInfo, setFutureInfo] = useState({});
  const [expanded, setExpanded] = useState({});
  const toggle = (c) => setExpanded(e => ({ ...e, [c]: !e[c] }));

  useEffect(() => {
    fetch('/api/flights?date=' + flightDate)
      .then(r => r.json())
      .then(data => {
        setFlights(data);
        fetch('/api/flights/future').then(f => f.json()).then(setFutureInfo).catch(() => setFutureInfo({}));
      })
      .catch(() => setFlights([]));
  }, [flightDate]);

  const shiftDay = (delta) => {
    setFlightDate(new Date(new Date(flightDate).getTime() + delta * 86400000).toISOString().split('T')[0]);
  };
  const today = () => setFlightDate(new Date().toISOString().split('T')[0]);

  return (
    <section style={sectionStyle}>
      <h3 style={{ margin: '0 0 14px', fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>Flight Schedule</h3>
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <input type="date" value={flightDate} onChange={e => setFlightDate(e.target.value)}
          style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: '#f8fafc', fontSize: 15 }} />
        <button onClick={() => shiftDay(-1)} style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#6366f1,#4f46e5)', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>◀ Previous Day</button>
        <button onClick={today} style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#f59e0b,#d97706)', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Today</button>
        <button onClick={() => shiftDay(1)} style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#6366f1,#4f46e5)', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Next Day ▶</button>
        <button disabled={fetchRunning} onClick={onFetchNow}
          style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: fetchRunning ? '#475569' : '#10b981', color: '#fff', fontWeight: 700, cursor: fetchRunning ? 'not-allowed' : 'pointer', fontSize: 13 }}>
          {fetchRunning ? 'Fetching...' : 'Fetch Now'}
        </button>
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
            <div style={{ marginTop: 8, padding: 8 }}>
              {expanded[airport] ? (
                <div>
                  <FlightTable
                    title={`Arrivals (${arr.length})`}
                    rows={arr} empty="No arrivals" firstLabel="From"
                    firstCol={a => a.from_icao ? (a.from_airport_name ? a.from_airport_name + ' (' + a.from_icao + ')' : (a.from_icao || a.airport_icao || airport)) : (a.airport_icao || airport)}
                  />
                  <div style={{ marginTop: 10 }}>
                    <FlightTable
                      title={`Departures (${dep.length})`}
                      rows={dep} empty="No departures" firstLabel="To"
                      firstCol={d => d.destination_name ? d.destination_name + ' (' + d.destination_icao + ')' : d.destination_icao}
                    />
                  </div>
                </div>
              ) : <span style={{ color: '#94a3b8', fontSize: 13 }}>Click to expand</span>}
            </div>
          </div>
        );
      })}
      {!list.length && <div style={{ color: '#94a3b8', fontSize: 14 }}>No airports saved yet.</div>}
    </section>
  );
}
