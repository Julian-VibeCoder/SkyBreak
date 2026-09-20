import React, { useEffect, useState } from 'react';
export default function App() {
  const [code, setCode] = useState('');
  const [list, setList] = useState([]);
  const [feedback, setFeedback] = useState('');
  useEffect(() => { fetch('/api/airports').then(r=>r.json()).then(setList).catch(()=>setList([])); }, []);
  const submit = async (e) => {
    e.preventDefault();
    const raw = code.trim().toUpperCase();
    if (!/^[A-Z0-9]{3}$/.test(raw)) { setFeedback('Ungültiger IATA-Code'); return; }
    const res = await fetch('/api/airports', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({code:raw}) });
    if (res.ok) { setFeedback('Gespeichert: '+raw); setList([...list, raw]); setCode(''); } else { setFeedback('Serverfehler'); }
  };
  return (<div style={{fontFamily:'sans-serif',padding:20}}><h1>SkyBreak — Airports</h1><form onSubmit={submit}><input value={code} maxLength={3} placeholder="LHR" onChange={e=>setCode(e.target.value.toUpperCase())}/><button type="submit">Speichern</button></form><p>{feedback}</p><ul>{list.map(c=><li key={c}>{c}</li>)}</ul></div>);
}
