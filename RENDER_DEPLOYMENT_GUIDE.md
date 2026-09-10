# Deploying BudgetFlow Backend to Render

This guide walks you through deploying the BudgetFlow Django backend to [Render](https://render.com/).

---

## Deployment Option 1: Manual Web Service (Recommended for simplicity)

1. **Push your code to GitHub / GitLab**.
2. Go to your [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Select your repository (`BudgetFlow`).
4. In the service creation form, configure the following settings:
   - **Name**: `budgetflow-backend` (or your preferred name)
   - **Region**: Choose the region closest to you (e.g., Singapore, Frankfurt, Oregon)
   - **Root Directory**: `backend` (if your repo has `backend/` and `frontend/` folders) or leave empty if deploying from a backend-only repo.
   - **Runtime**: `Python 3`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn budgetflow_backend.wsgi:application`
   - **Instance Type**: `Free`

5. **Add Environment Variables** (under "Advanced" -> "Environment Variables"):
   - `PYTHON_VERSION`: `3.12.4`
   - `SECRET_KEY`: *Click "Generate" or enter a secure random string*
   - `DEBUG`: `False`
   - `CORS_ALLOW_ALL_ORIGINS`: `True` (or set `CORS_ALLOWED_ORIGINS` to your frontend domain)
   - `DATABASE_URL`: *(Leave empty if using SQLite or paste your PostgreSQL connection string from step 6)*

6. **Set up a PostgreSQL Database on Render (Optional but Recommended)**:
   - In Render Dashboard, click **New +** -> **PostgreSQL**.
   - Set **Name**: `budgetflow-db`, **Plan**: `Free`.
   - Once provisioned, copy the **Internal Database URL**.
   - Go back to your `budgetflow-backend` Web Service -> **Environment**, and set `DATABASE_URL` to the copied internal database URL.

7. **Click Deploy Web Service**.

---

## Deployment Option 2: Render Blueprint (Infrastructure as Code)

1. Ensure `render.yaml` is in your repository.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml` and configure both the Web Service and PostgreSQL database automatically.
4. Click **Apply**.

---

## Post-Deployment Tasks (Render Shell)

Once your web service is deployed and status is **Live**, open the **Shell** tab in the Render Dashboard for your service:

### 1. Create an Admin Superuser
```bash
python manage.py createsuperuser
```
Follow the prompts to enter username, email, and password.

### 2. Seed Initial Financial Data (Optional)
If you wish to populate initial categories and mock data:
```bash
python manage.py seed_data
```

### 3. Verify Health Check
Visit:
```
https://<your-service-name>.onrender.com/api/health/
```
You should receive:
```json
{
  "status": "healthy",
  "service": "BudgetFlow Backend API",
  "version": "1.0.0"
}
```

---

## Connecting the Frontend

In your frontend project (e.g. Next.js), update the backend API base URL environment variable:
```env
NEXT_PUBLIC_API_URL=https://<your-service-name>.onrender.com/api
```
