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
landslide risk indices. Cyclone likelihood is not estimated because this feed
does not provide an authoritative cyclone track. Location-prediction history
can optionally be saved to MongoDB Atlas:

1. Create a MongoDB Atlas cluster and a database user.
2. Allow the Render service to connect in the cluster's Network Access settings.
   Restrict allowed IP ranges where your hosting plan supports stable egress IPs.
3. Copy the Atlas connection string and set it as `MONGODB_URI` in the Render
   service environment. Set `MONGODB_DATABASE` to `disasterguard` or another
   database name. Keep the URI private.

Without `MONGODB_URI`, live forecasts still work, but prediction history is not
stored. With MongoDB configured, prediction records expire after 90 days.
