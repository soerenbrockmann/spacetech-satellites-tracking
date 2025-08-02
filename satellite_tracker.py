import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from skyfield.api import load, wgs84, EarthSatellite
import requests
from datetime import datetime

LAT = 40.7128
LON = -74.0060
ELEV = 10
SAT_NAME = "ISS (ZARYA)"
UPDATE_INTERVAL = 5  # seconds

# --- DOWNLOAD TLE ---
TLE_URL = "https://celestrak.org/NORAD/elements/stations.txt"
tle_data = requests.get(TLE_URL).text.splitlines()
lines = {}
for i, line in enumerate(tle_data):
    if line.strip() == SAT_NAME:
        lines['name'] = line
        lines['l1'] = tle_data[i+1]
        lines['l2'] = tle_data[i+2]
        break
if not lines:
    print(f"Satellite '{SAT_NAME}' not found!")
    exit()

ts = load.timescale()
satellite = EarthSatellite(lines['l1'], lines['l2'], lines['name'], ts)
observer = wgs84.latlon(LAT, LON, ELEV)

fig = plt.figure(figsize=(8,8))
ax = plt.subplot(111, polar=True)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_rlim(0, 90)
ax.set_rlabel_position(135)
ax.set_title(f"Real-Time {SAT_NAME} Sky Track", va='bottom')

visible_line, = ax.plot([], [], 'r-', lw=2, label='Visible path')
hidden_line, = ax.plot([], [], 'k--', lw=1, alpha=0.3, label='Below horizon')
marker, = ax.plot([], [], 'ro', markersize=8)
plt.legend(loc='upper right')

def compute_orbit_path():
    alts, azs, visibility = [], [], []
    t0 = ts.now()
    for minutes in range(0, 180, 2):  # simulate 3 hours to see orbit
        t = t0 + minutes / (24*60)
        topocentric = (satellite - observer).at(t)
        alt, az, _ = topocentric.altaz()
        # Clip altitude to 0-90 for plotting
        alt_deg = max(0, min(alt.degrees, 90))
        alts.append(alt_deg)
        azs.append(az.degrees)
        visibility.append(alt.degrees > 0)
    return np.radians(azs), 90 - np.array(alts), np.array(visibility)

az_path, alt_path, visibility = compute_orbit_path()

def update(frame):
    t = ts.now()
    topocentric = (satellite - observer).at(t)
    alt, az, _ = topocentric.altaz()

    print(f"Time {datetime.utcnow().strftime('%H:%M:%S')} | Alt={alt.degrees:.1f}°, Az={az.degrees:.1f}°")

    # Update marker
    marker.set_data([np.radians(az.degrees)], [90 - max(0, min(alt.degrees, 90))])

    # Update orbit paths
    visible_line.set_data(az_path[visibility], alt_path[visibility])
    hidden_line.set_data(az_path[~visibility], alt_path[~visibility])

    ax.set_title(f"{SAT_NAME} @ {datetime.utcnow().strftime('%H:%M:%S UTC')}\n"
                 f"Alt: {alt.degrees:.1f}° Az: {az.degrees:.1f}°", va='bottom')
    return visible_line, hidden_line, marker

ani = FuncAnimation(fig, update, interval=UPDATE_INTERVAL*1000)
plt.show()
