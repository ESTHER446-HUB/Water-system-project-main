# Deployment Guide - Smart Irrigation System v3.0

## Option 1: Raspberry Pi (Recommended for Hardware)

### Automatic Deployment:
```bash
./deploy_pi.sh
```

### Manual Deployment:
```bash
# 1. Install dependencies
pipenv install Flask flask-cors requests gunicorn

# 2. Copy service file
sudo cp irrigation.service /etc/systemd/system/

# 3. Update paths in service file
sudo nano /etc/systemd/system/irrigation.service

# 4. Enable and start
sudo systemctl enable irrigation.service
sudo systemctl start irrigation.service

# 5. Check status
sudo systemctl status irrigation
```

### Access:
- Local: `http://localhost:5000`
- Network: `http://[PI_IP]:5000`

---

## Option 2: Cloud Deployment (Render)

### Steps:
1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create new Web Service
4. Connect your GitHub repo
5. Render will auto-detect `render.yaml`
6. Deploy!

**Note:** Hardware features won't work in cloud

---

## Option 3: Docker Deployment

```bash
# Build image
docker build -t irrigation-system .

# Run container
docker run -d -p 5000:5000 --name irrigation irrigation-system

# Access at http://localhost:5000
```

---

## Option 4: Heroku Deployment

### Create Procfile:
```
web: gunicorn app:app
```

### Deploy:
```bash
heroku login
heroku create irrigation-system
git push heroku main
heroku open
```

---

## Option 5: Local Network Access

Already running! Access from any device on your network:

1. Find your IP:
```bash
hostname -I
```

2. Access from phone/tablet:
```
http://[YOUR_IP]:5000
```

---

## Production Checklist

- [ ] Change secret key in `app.py`
- [ ] Change default admin password
- [ ] Set up SSL/HTTPS (use nginx + certbot)
- [ ] Configure firewall
- [ ] Set up automatic backups for `irrigation.db`
- [ ] Configure email notifications (SMTP settings)
- [ ] Test all sensors and pumps
- [ ] Set up monitoring/alerts

---

## Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Service won't start:
```bash
sudo journalctl -u irrigation -n 50
```

### Check if port is in use:
```bash
sudo lsof -i :5000
```

### Restart service:
```bash
sudo systemctl restart irrigation
```

### View live logs:
```bash
sudo journalctl -u irrigation -f
```

---

## Auto-start on Boot

Already configured with systemd service!

To disable:
```bash
sudo systemctl disable irrigation
```

To re-enable:
```bash
sudo systemctl enable irrigation
```
