import { useState, useEffect } from 'react';

// Loads the saved-airport list plus a code -> name map. The list is shared by
// the Airports, Flights and Trips tabs, so it lives here and is passed down.
export function useAirports() {
  const [list, setList] = useState([]);
  const [airportNames, setAirportNames] = useState({});
  useEffect(() => {
    fetch('/api/airports')
      .then(r => r.json())
      .then(data => {
        const items = Array.isArray(data) ? data : [];
        const codes = items.map(c => (typeof c === 'string' ? c : c.code || c));
        setList(codes);
        const nameMap = {};
        items.forEach(item => {
          const code = typeof item === 'string' ? item : item.code || item;
          const name = typeof item === 'string' ? '' : (item.name || '');
          if (code) nameMap[code] = name || code;
        });
        setAirportNames(nameMap);
      })
      .catch(() => setList([]));
  }, []);
  return { list, setList, airportNames };
}
