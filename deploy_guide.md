# Production Deployment Guide: D2R Item Database

We have provided all the files necessary to "package" the project for professional deployment.

## 📦 Option 1: Docker Deployment (Recommended)
This is the most reliable way to package the application, as it bundles Python, all libraries (including OCR dependencies), and configuration into a single "container".

### 1. Configure Secrets
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Ensure you set:
- `SECRET_KEY`: A long, random string.
- `GEMINI_API_KEY`: Your Google AI key.
- `ENVIRONMENT`: Set to `production`.

### 2. Launch with Docker Compose
Run the following command to build and start the containers:
```bash
docker-compose up -d --build
```
Your deployment now consists of two primary portals:
- **Main Application**: `http://localhost:5000`
- **Admin Utility**: `http://localhost:5001`

### 3. Data Persistence
The `docker-compose.yml` ensures that:
- `d2r_items.db`: The database is stored on your host machine.
- `static/uploads`: User-uploaded item screenshots are persistent.
- `static/items`: Item images uploaded via the Admin panel are persistent.
- `settings.json`: Your app settings are preserved.

---

## 🪟 Option 2: Windows Native Deployment (Manual)
If you prefer not to use Docker, use the **Waitress** WSGI server (which we added to `requirements.txt`).

1. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
2. **Start the Production Server**:
   Create a small script (e.g., `run_prod.py`) or run directly:
   ```powershell
   waitress-serve --port=5000 app:app
   ```
   > [!NOTE]
   > On Windows, ensure you have the `ENVIRONMENT=production` environment variable set so that `WhiteNoise` performs optimally.

---

## 🔒 Security Best Practices

### SSL/HTTPS
Neither Gunicorn nor Waitress should be used to serve HTTPS directly.
- **Docker**: Put a reverse proxy like **Nginx** or **Traefik** in front of your containers.
- **Windows**: Use **IIS** as a reverse proxy or **Caddy** for automatic SSL.

### Environment Management
- ✅ Never commit your `.env` file to a public repository.
- ✅ Use a strong, unique `SECRET_KEY` to prevent session tampering.
- ✅ In production, ensure `DEBUG` is effectively `False` (the app now checks the `ENVIRONMENT` var).

## ✅ Verification
After deploying:
1. Visit the `/` page and check the network tab. Static files should have `Cache-Control` headers (served by `WhiteNoise`).
2. Log in and verify sessions persist.
3. Upload an item image and verify it appears in `static/uploads`.
