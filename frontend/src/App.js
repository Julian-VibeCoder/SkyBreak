import React, { useEffect, useState } from 'react';
import CollapsibleSidebar from './components/CollapsibleSidebar';
import AirportsTab from './components/AirportsTab';
import FlightsTab from './components/FlightsTab';
import TripsTab from './components/TripsTab';
import FavoriteTripPrices from './components/FavoriteTripPrices';
import SettingsTab from './components/SettingsTab';
import { useActiveTab } from './hooks/useActiveTab';
import { useAirports } from './hooks/useAirports';

const NAV = [
  { key: 'trips', label: 'Trips', icon: '🧳' },
  { key: 'favorites', label: 'Favorites', icon: '⭐' },
  { key: 'airports', label: 'Airports', icon: '✈️' },
  { key: 'flights', label: 'Flights', icon: '🛫' },
  { key: 'settings', label: 'Settings', icon: '⚙️' },
];

// App shell: routing, responsive sidebar, and the shared airport list that the
// per-tab components consume. Each tab owns its own data + interactions.
export default function App() {
  const [tab, setTab] = useActiveTab(NAV);
  const [mobileNavHidden, setMobileNavHidden] = useState(typeof window !== 'undefined' ? window.innerWidth < 1024 : false);
  const { list, setList, airportNames } = useAirports();
  const [scrapeRunning, setScrapeRunning] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) setMobileNavHidden(true);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Poll the scraper status while it runs; stop once it finishes.
  useEffect(() => {
    const check = () => {
      fetch('/api/flights/scrape-status')
        .then(r => r.json())
        .then(d => {
          setScrapeRunning(!!d.running);
          if (d.running) setTimeout(check, 2000);
        })
        .catch(() => setScrapeRunning(false));
    };
    check();
  }, []);

  const handleFetchNow = () => {
    fetch('/api/flights/fetch-now', { method: 'POST' }).then(() => alert('Fetch started'));
  };

  const selectTab = (n) => {
    setTab(n.key);
    if (typeof window !== 'undefined' && window.innerWidth < 1024) setMobileNavHidden(true);
    window.history.pushState({}, '', '/' + n.key);
  };

  return (
    <div style={{
      display: 'flex', flexDirection: 'row', minHeight: '100dvh', fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#f1f5f9'
    }}>
      <CollapsibleSidebar collapsed={mobileNavHidden} onToggle={() => setMobileNavHidden(c => !c)}><aside style={{
        width: 220, flexShrink: 0, background: 'rgba(15,23,42,0.85)',
        backdropFilter: 'blur(12px)', borderRight: '1px solid rgba(255,255,255,0.06)',
        padding: '18px 14px', display: 'flex', flexDirection: 'column', gap: 10,
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
            <a key={n.key} href={'/' + n.key} onClick={(e) => { if (e.ctrlKey || e.metaKey || e.button === 1) return; e.preventDefault(); selectTab(n); }} style={{ textDecoration: 'none', color: 'inherit', display: 'block', width: '100%' }}>
              <button style={{
                width: '100%', textAlign: 'left', padding: '12px 14px', borderRadius: 12, border: 'none',
                background: tab === n.key ? 'rgba(56,189,248,0.15)' : 'transparent',
                color: tab === n.key ? '#38bdf8' : '#cbd5e1', fontWeight: 600, fontSize: 15,
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12,
                transition: 'all 0.2s ease', boxShadow: tab === n.key ? 'inset 0 0 0 1px rgba(56,189,248,0.35)' : 'none'
              }}>
                <span style={{ fontSize: 18 }}>{n.icon}</span>
                {n.label}
              </button>
            </a>
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{ fontSize: 34, lineHeight: 1 }}>✈️</span>
            <div>
              <h2 style={{ margin: 0, fontSize: 28, fontWeight: 800, letterSpacing: '-0.8px' }}>
                Skybreak Travel Dashboard
              </h2>
            </div>
          </div>
        </header>

        <div style={{ display: 'grid', gap: 24, gridTemplateColumns: '1fr', alignItems: 'start' }}>
          {tab === 'trips' && <TripsTab list={list} airportNames={airportNames} />}

          {tab === 'favorites' && (
            <section style={{
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 18, padding: 24, boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
            }}>
              <FavoriteTripPrices />
            </section>
          )}

          {tab === 'airports' && <AirportsTab list={list} setList={setList} />}

          {tab === 'flights' && <FlightsTab list={list} onFetchNow={handleFetchNow} fetchRunning={scrapeRunning} />}

          {tab === 'settings' && <SettingsTab />}
        </div>
      </main>
    </div>
  );
}
