# Deploying Diggy Func on AWS EC2

Step-by-step guide to deploy this FastAPI app on a bare-metal EC2 instance.

---

## Prerequisites

- An **AWS account**
- A terminal with **SSH** access

---

## Step 1 — Launch an EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**
2. Configure:
   | Setting | Value |
   |---------|-------|
   | **AMI** | Ubuntu Server 22.04 LTS |
   | **Instance type** | `t2.micro` (free tier) or `t3.small` for better perf |
   | **Key pair** | Create or select an existing `.pem` key |
   | **Storage** | 20 GB gp3 (default is fine) |

3. Under **Network settings → Security Group**, allow these inbound rules:

   | Port | Protocol | Source | Purpose |
   |------|----------|--------|---------|
   | 22   | TCP      | Your IP | SSH access |
   | 80   | TCP      | 0.0.0.0/0 | HTTP traffic |
   | 443  | TCP      | 0.0.0.0/0 | HTTPS (optional) |

4. Click **Launch Instance** and wait for it to be running.

---

## Step 2 — Connect to Your Instance

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

---

## Step 3 — Clone the Repo

```bash
sudo apt-get install -y git
git clone <YOUR_REPO_URL> /tmp/diggy_func_aws
cd /tmp/diggy_func_aws
```

> If the repo is private, use a GitHub personal access token or deploy key.

---

## Step 4 — Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Fill in your actual keys:
```
SERP_API_KEY=your_actual_serpapi_key
GROQ_API_KEY=your_actual_groq_key
```

---

## Step 5 — Run the Setup Script

```bash
sudo bash deploy/setup.sh
```

This script will:
- Install Python 3, pip, Nginx
- Create a Python virtual environment at `/opt/diggy_func_aws/venv`
- Install all pip dependencies
- Copy your app to `/opt/diggy_func_aws`
- Configure and start the **systemd** service
- Configure and start **Nginx** as a reverse proxy

---

## Step 6 — Verify Deployment

Check service status:
```bash
sudo systemctl status diggy
```

Test the endpoint:
```bash
curl -X POST http://<EC2_PUBLIC_IP>/summary \
  -H "Content-Type: application/json" \
  -d '{"query": "latest tech news"}'
```

You should get a JSON response with `"status": "success"`.

---

## Useful Commands

| Action | Command |
|--------|---------|
| View logs | `sudo journalctl -u diggy -f` |
| Restart app | `sudo systemctl restart diggy` |
| Stop app | `sudo systemctl stop diggy` |
| Restart Nginx | `sudo systemctl restart nginx` |

---

## Optional — Add HTTPS with Certbot

If you have a domain name pointing to your EC2 IP:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Certbot will automatically update Nginx config and set up auto-renewal.

---

## Updating the App

To deploy code changes:

```bash
cd /tmp/diggy_func_aws    # or wherever you cloned
git pull

# Copy updated files
sudo cp main.py schemas.py requirements.txt /opt/diggy_func_aws/
sudo cp -r api /opt/diggy_func_aws/

# Reinstall deps if requirements changed
sudo /opt/diggy_func_aws/venv/bin/pip install -r /opt/diggy_func_aws/requirements.txt

# Restart
sudo systemctl restart diggy
```

---

## Cleanup

To remove everything and avoid charges:

1. Go to **EC2 Console → Instances**
2. Select your instance → **Instance state → Terminate instance**
