# Docker Desktop for Windows Guide: D2R Item Database

Since you are using **Docker Desktop on Windows**, it's important to understand that your **host** is Windows, but the **container** (the package) runs a lightweight Linux environment (via WSL2). This is the standard and most efficient way to deploy Python apps.

## 🚀 Deployment Steps (Windows Host)

1. **Environment Setup**:
   Open **PowerShell** in `c:\OpenCode\D2RItemDB`:
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` and set your `SECRET_KEY` and `GEMINI_API_KEY`.

2. **Launch with Docker Compose**:
   ```powershell
   docker-compose up -d --build
   ```
   > [!NOTE]
   > Even though you see `gunicorn` and `apt-get` in the `Dockerfile`, these are execution instructions for the **inside** of the container. Docker Desktop handles the translation perfectly on your Windows machine.

3. **Access the App**:
   Visit `http://localhost:5000`.

---

## 🖥️ Managing via Docker Desktop GUI

Docker Desktop provides a powerful dashboard for Windows users:

### 1. Containers Tab
- Look for the `d2r-item-db` stack.
- **Logs**: Click the container to see the server output. If you see "Gunicorn is running", your app is live!
- **Inspect**: Check the **Mounts** section. You should see your local `c:\OpenCode\D2RItemDB` folders mapped to `/app` inside the container.

### 2. Images Tab
- You'll see an image named `d2r-item-db-app`. This is your "Packaged" application. It contains all dependencies (EasyOCR, Flask, Gemini SDK) in a pre-configured state.

### 3. Settings (Important for Windows)
- **General**: Ensure "Use the WSL 2 based engine" is checked.
- **Resources > File Sharing**: Docker Desktop usually handles this automatically now, but if you get a "Mount Denied" error, make sure `C:\OpenCode\D2RItemDB` is allowed here.

---

## 🛠️ Windows vs. Container Paths

Your files are shared between Windows and the Container:
| Feature | Windows Path (Your Host) | Container Path (The App) |
| :--- | :--- | :--- |
| **Database** | `.\d2r_items.db` | `/app/d2r_items.db` |
| **Uploads** | `.\static\uploads\` | `/app/static/uploads/` |
| **Logs** | Viewed in Docker Desktop | `/dev/stdout` |

## ✅ Final Verification
1. Open Docker Desktop.
2. Ensure the status icon (bottom left) is **green**.
3. Run the `up` command in PowerShell.
4. If you see the "whale" icon in the taskbar and the container is "Running" in the dashboard, your D2R Database is successfully deployed!
