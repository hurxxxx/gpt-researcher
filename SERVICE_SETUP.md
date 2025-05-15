# GPT Researcher Service Setup

This document explains how to use the provided scripts to manage the GPT Researcher application and set it up as a system service.

## Using the Run Script

The `run.sh` script provides a convenient way to start, stop, restart, and check the status of both the backend server and the Next.js frontend.

### Basic Usage

```bash
# Start both backend and frontend
./run.sh start

# Stop both services
./run.sh stop

# Restart both services
./run.sh restart

# Check the status of the services
./run.sh status
```

### Configuration

By default, the script is configured to use the "gpt-researcher" conda environment. If you need to change this, edit the `CONDA_ENV` variable in the `run.sh` file.

## Setting Up as a System Service

The `gpt-researcher.service` file allows you to register GPT Researcher as a system service using systemd.

### Installation Steps

1. Edit the service file to match your username and installation path if needed:

```bash
nano gpt-researcher.service
```

2. Copy the service file to the systemd directory:

```bash
sudo cp gpt-researcher.service /etc/systemd/system/
```

3. Reload the systemd daemon to recognize the new service:

```bash
sudo systemctl daemon-reload
```

4. Enable the service to start on boot:

```bash
sudo systemctl enable gpt-researcher.service
```

5. Start the service:

```bash
sudo systemctl start gpt-researcher.service
```

### Managing the Service

```bash
# Start the service
sudo systemctl start gpt-researcher.service

# Stop the service
sudo systemctl stop gpt-researcher.service

# Restart the service
sudo systemctl restart gpt-researcher.service

# Check the status
sudo systemctl status gpt-researcher.service

# View logs
sudo journalctl -u gpt-researcher.service
```

## Troubleshooting

### Service Won't Start

1. Check the logs:
```bash
sudo journalctl -u gpt-researcher.service -n 50
```

2. Verify the paths in the service file match your installation.

3. Make sure the run.sh script has execute permissions:
```bash
chmod +x /path/to/run.sh
```

4. Try running the script manually to see any errors:
```bash
./run.sh start
```

### Port Conflicts

The backend uses port 8000 and the frontend uses port 3000. If these ports are already in use, the services won't start. You can modify the ports in:

- Backend: Edit the `run.sh` file to change the port in the uvicorn command
- Frontend: Edit the Next.js configuration in `frontend/nextjs/next.config.mjs`

## Notes

- The run script creates PID files in the project directory to track running processes.
- The service is configured to restart automatically if it fails.
- Both the backend and frontend are started as background processes.
