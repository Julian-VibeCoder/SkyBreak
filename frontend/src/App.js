import React, { useEffect, useState } from 'react';
export default function App() {
  const [code, setCode] = useState('');
  const [list, setList] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [flights, setFlights] = useState([]);
  useEffect(() => { fetch('/api/flights').then(r=>r.json()).then(setFlights).catch(()=>setFlights([])); }, []);
  const submit = async (e) => {
    e.preventDefault();
    const raw = code.trim().toUpperCase();
    if (!/^[A-Z0-9]{3}$/.test(raw)) { setFeedback('Ungültiger IATA-Code'); return; }
    const res = await fetch('/api/airports', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({code:raw}) });
    if (res.ok) { setFeedback('Gespeichert: '+raw); setList([...list, raw]); setCode(''); } else { setFeedback('Serverfehler'); }
  };
  return (<div style={{fontFamily:'sans-serif',padding:20}}><h1>SkyBreak — Airports</h1><form onSubmit={submit}><input value={code} maxLength={3} placeholder="LHR" onChange={e=>setCode(e.target.value.toUpperCase())}/><button type="submit">Speichern</button></form><p>{feedback}</p><ul>{list.map(c=><li key={c}>{c}</li>)}</ul><h2>Flüge (1 Jahr Zukunft)</h2>
<input type="date" id="flightDate" onChange={(e) => { const d = e.target.value; fetch('/api/flights?date=' + d).then(r=>r.json()).then(d=>setFlights(d)).catch(()=>{}); }} />
<ul>{flights.map(f=><li key={f.airport_icao+f.destination_icao}>{f.airport_icao} ({f.airport_name||''}) → {f.destination_icao} ({f.destination_name||''}) | {f.direction}</li>)}</ul></div>);
}
