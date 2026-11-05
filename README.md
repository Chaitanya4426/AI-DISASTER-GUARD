# AI DisasterGuard

Flask dashboard for demo disaster-risk monitoring, weather, and user registration.
Location outlooks use live Open-Meteo forecasts and nearby elevation data with a
transparent heuristic. They are risk indices, not calibrated probabilities,
trained AI predictions, or official emergency guidance. The dashboard's sample
alerts remain demo data.

## Run locally

```powershell
$env:SECRET_KEY = [guid]::NewGuid().ToString()
python -m pip install -r requirements.txt
python -m flask --app app run
```

Open http://127.0.0.1:5000.

## Deploy on Render

1. In Render, create a **Blueprint** and select this GitHub repository.
2. Deploy using `render.yaml`; Render generates the required `SECRET_KEY`.
3. Open the service's `onrender.com` URL after the first deploy completes.

The free service uses SQLite in its ephemeral filesystem. User accounts and other
database changes can be lost when the service restarts or redeploys. Use a
persistent database before relying on stored accounts.

On the Weather page, search for a place or enter coordinates to see flood and
landslide risk indices. The weather forecast uses Open-Meteo and nearby elevation
data. Nearby tropical cyclone event reports come from GDACS and are displayed
only while reported active and within 750 km of the reported event center; this
is not a forecast track or location-impact probability. Recent earthquakes
within 300 km are queried from the USGS feed for the previous seven days.
Earthquakes cannot be predicted; recent events are observations, not a forecast.
Provider outages and stale reports are possible, so always follow official
local meteorological, emergency, and geological authorities.

Flood and landslide percentages are heuristic risk indices, not calibrated
probabilities, trained AI predictions, or official warnings. The flood response
guide is preparedness information only. The app does not send SMS, issue public
warnings, dispatch responders, manage a live supply inventory, or restore
infrastructure. Flood and landslide risk indices can optionally be saved to
MongoDB Atlas; nearby USGS and GDACS event observations are not stored:

1. Create a MongoDB Atlas cluster and a database user.
2. Allow the Render service to connect in the cluster's Network Access settings.
   Restrict allowed IP ranges where your hosting plan supports stable egress IPs.
3. Copy the Atlas connection string and set it as `MONGODB_URI` in the Render
   service environment. Set `MONGODB_DATABASE` to `disasterguard` or another
   database name. Keep the URI private.

Without `MONGODB_URI`, live forecasts still work, but prediction history is not
stored. With MongoDB configured, prediction records expire after 90 days.
