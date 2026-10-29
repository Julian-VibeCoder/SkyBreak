export function formatTime(ts) {
  if (!ts) return '-';
  const m = ts.match(/(\d{1,2}):(\d{2})/);
  if (m) return m[1] + ':' + m[2];
  return ts.includes(':') ? ts.split(':').slice(0, 2).join(':') : '-';
}

export function formatTripDateTime(dt) {
  if (!dt) return '-';
  return dt.substring(0, 10) + ', ' + dt.substring(11, 16);
}
