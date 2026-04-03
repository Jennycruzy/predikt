# PREDIKT VPS Daemon Setup

To ensure your GenLayer intelligent contracts are populated fully autonomously 24/7 without your laptop being open, you can deploy the Python daemon to any standard Linux VPS (like DigitalOcean, AWS EC2, or Hetzner).

## 1. Prepare your VPS
Connect to your VPS via SSH and clone this repository.
```bash
git clone <your-repo-url>
cd PREDIKT/backend
```

## 2. Install Dependencies
Ensure Python 3 is installed. Then install the Web3 and AI frameworks.
```bash
python3 -m pip install -r requirements.txt
python3 -m pip install web3 openai
```

## 3. Secure your Keys
Create your `.env` file in the root `PREDIKT/` folder, just like you have locally.
```bash
nano ../.env
```
Ensure these two keys are populated:
```env
OWNER_PRIVATE_KEY=your_deployer_wallet_private_key_with_sepolia_eth
VENICE_API_KEY=your_venice_ai_admin_key
```

## 4. Set up a `systemd` Service (Recommended)
By using `systemd`, your VPS will automatically restart the daemon if it crashes, and automatically start it when the server reboots!

Create a service file:
```bash
sudo nano /etc/systemd/system/predikt-daemon.service
```

Paste the following (adjust `ExecStart` and `WorkingDirectory` to map to where you cloned the repo):
```ini
[Unit]
Description=Predikt Market Generator Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/PREDIKT/backend
ExecStart=/usr/bin/python3 /root/PREDIKT/backend/market_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 5. Enable and Start the Daemon
Reload `systemd` so it sees your new file:
```bash
sudo systemctl daemon-reload
```

Enable the daemon to run on boot:
```bash
sudo systemctl enable predikt-daemon
```

Start the daemon right now:
```bash
sudo systemctl start predikt-daemon
```

## 6. Monitor the Logs
You can watch the GenLayer bridging logs live at any time to verify the AI is successfully making the markets:
```bash
sudo journalctl -u predikt-daemon -f
```

That's it! Your private prediction markets platform is now **100% autonomous and fully decentralized**.
