# Deployment Guide

## Step 1: Push to GitHub

```bash
cd /home/esther-kuria/Desktop/PHASE-FIVE/Watersystem/Water-system-project-main

# Initialize git (already done)
git add .
git commit -m "Smart Irrigation System"

# Create new repo on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/irrigation-system.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render

1. Go to **https://render.com**
2. Sign up/Login (free)
3. Click **"New +"** → **"Web Service"**
4. Click **"Connect GitHub"** → Authorize
5. Select **"irrigation-system"** repo
6. Configure:
   - **Name:** `irrigation-system`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** `Free`
7. Click **"Create Web Service"**

## Step 3: Wait (2-3 minutes)

Render will:
- Clone your repo
- Install dependencies
- Start the app
- Give you a URL

## Step 4: Access Your App

URL: `https://irrigation-system-XXXX.onrender.com`

Login:
- Username: `admin`
- Password: `admin123`

## Done! 🎉

Your app is live and accessible worldwide.

## Notes

- Free tier sleeps after 15 min inactivity
- First request after sleep takes ~30 seconds
- Database resets on redeploy (use paid plan for persistence)
