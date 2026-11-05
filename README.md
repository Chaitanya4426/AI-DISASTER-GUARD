# AI DisasterGuard

Flask dashboard for demo disaster-risk monitoring, weather, and user registration.
Risk estimates and alert feeds are demo data, not operational emergency guidance.

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
persistent database before relying on stored data.
