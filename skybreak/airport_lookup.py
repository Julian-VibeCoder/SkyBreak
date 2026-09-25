import csv, urllib.request
URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
_airport_cache = {}

def fetch_airport_name(iata_code: str) -> str:
    code = iata_code.upper()
    if code in _airport_cache:
        return _airport_cache[code]
    try:
        with urllib.request.urlopen(URL, timeout=15) as resp:
            reader = csv.reader(resp.read().decode('utf-8', errors='ignore').splitlines())
            for row in reader:
                if len(row) >= 5:
                    iata_field = row[4] if len(row) > 4 else ""
                    if iata_field and iata_field.strip().upper() == code:
                        name = row[1] if len(row) > 1 else ""
                        city = row[2] if len(row) > 2 else ""
                        country = row[3] if len(row) > 3 else ""
                        full = name.strip('"') if name else ""
                        if city or country:
                            extra = ", ".join(filter(None, [city.strip('"'), country.strip('"')]))
                            full += (" (" + extra + ")") if extra else ""
                        _airport_cache[code] = full
                        return _airport_cache[code]
        _airport_cache[code] = ""
        return ""
    except Exception:
        _airport_cache[code] = ""
        return ""
