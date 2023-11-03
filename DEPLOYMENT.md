## Astro-Shoots Deployment Guide

Astro-Shoots is a Flask-based project designed to calculate the optimal number of untracked photographs for capturing deep space objects (DSOs). This guide will walk you through the process of creating a service file on Linux to launch the Astro-Shoots application.

### Creating the Service File

Here's the service file for the Astro-Shoots application:

```bash
[Unit]
Description=Gunicorn instance to serve astro-shoots
After=network.target

[Service]
User=your-user
Group=your-group
WorkingDirectory=/path/to/your/project/
Environment="PYTHONPATH=/path/to/your/project/src"
ExecStart=/bin/bash -c 'source /path/to/your/project/venv/bin/activate && exec /path/to/your/project/venv/bin/gunicorn --workers=3 --bind 127.0.0.1:8005 src.app.application:app' --error-logfile /path/to/your/project/gunicorn_error.log

[Install]
WantedBy=multi-user.target
```

Replace `your-user` and `your-group` with the user and group that will run the service. Replace `/path/to/your/project/` with the actual path to your project on your server.

### Deploying the Service

To deploy the service, follow these steps:

1. Create a new file in the `/etc/systemd/system/` directory named `astro-shoots.service`.

2. Open the file in a text editor and paste the service file content into it.

3. Replace `your-user`, `your-group`, and `/path/to/your/project/` with the appropriate values.

4. Save and close the file.

5. Run the following command to reload the systemd manager configuration: `sudo systemctl daemon-reload`

6. Run the following command to enable the service to start on boot: `sudo systemctl enable astro-shoots`

7. Run the following command to start the service: `sudo systemctl start astro-shoots`

You can check the status of the service at any time by running: `sudo systemctl status astro-shoots`

Congratulations! You've successfully deployed the Astro-Shoots application as a service on Linux.
