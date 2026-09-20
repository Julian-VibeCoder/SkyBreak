import React, { useEffect, useState } from 'react';
export default function App() {
  const [code, setCode] = useState('');
  const [list, setList] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [flights, setFlights] = useState([]);
  const [flightDate, setFlightDate] = useState('');

  useEffect(() => {
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
    fetch(url).then(r => r.json()).then(setFlights).catch(() => setFlights([]));
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
    <div style={{fontFamily:'sans-serif',padding:20}}>
      <h1>SkyBreak — Airports</h1>
      <form onSubmit={submit}>
        <input id="codeInput" value={code} maxLength={3} placeholder="LHR" onChange={e => setCode(e.target.value.toUpperCase())}/>
        <button type="submit">Speichern</button>
      </form>
      <p>{feedback}</p>
      <ul>
        {list.map(c => <li key={c}>{c} <button onClick={() => removeAirport(c)}>×</button></li>)}
      </ul>
      <h2>Abflüge & Ankünfte</h2>
      <input type="date" value={flightDate} onChange={e => { setFlightDate(e.target.value); loadFlights(); }} />
      <ul>
        {flights.map(f => <li key={f.airport_icao+f.destination_icao}>{f.airport_icao} ({f.airport_name||''}) → {f.destination_icao} ({f.destination_name||''}) | {f.direction}</li>)}
      </ul>
    </div>
  );
}
