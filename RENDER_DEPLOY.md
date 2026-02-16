# 🚀 Deploy to Render - Step by Step

## Prerequisites
- GitHub account
- Render account (free at render.com)

## Step 1: Push to GitHub

```bash
cd /home/esther-kuria/Desktop/PHASE-FIVE/Watersystem/Water-system-project-main

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Smart Irrigation System v3.0"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/irrigation-system.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render

1. Go to **https://render.com** and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select your **irrigation-system** repository
5. Configure:
   - **Name:** `irrigation-system`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan:** `Free`
6. Click **"Create Web Service"**

## Step 3: Wait for Deployment

Render will:
- Install dependencies
- Build your app
- Deploy it
- Give you a URL like: `https://irrigation-system.onrender.com`

## Step 4: Access Your App

Open the URL Render provides and login with:
- Username: `admin`
- Password: `admin123`

## ⚠️ Important Notes

### Free Tier Limitations:
- App sleeps after 15 min of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month free

### Database:
- SQLite works but resets on each deploy
- For persistent data, upgrade to paid plan or use external DB

### Hardware Features:
- Sensor/pump GPIO won't work (cloud has no hardware)
- System runs in simulation mode
- Perfect for testing the UI/dashboard

## 🔧 Troubleshooting

### Build fails?
Check logs in Render dashboard

### App won't start?
Verify `requirements.txt` has all dependencies

### Database resets?
Use Render's PostgreSQL add-on (paid) or external DB

## 🎉 You're Live!

Your irrigation system is now accessible worldwide at your Render URL!

Share it with: `https://YOUR-APP.onrender.com`
