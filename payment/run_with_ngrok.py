import os
import subprocess

from pyngrok import conf, ngrok


"""
This script runs the Django development server and exposes it to the internet
using ngrok. It automatically sets the ngrok auth token if provided in the
environment variable `NGROK_AUTH`, starts a public ngrok tunnel on port 8000,
and then runs the Django server on 0.0.0.0:8000.
"""

if __name__ == "__main__":
    auth_token = os.getenv("NGROK_AUTH")
    if auth_token:
        conf.get_default().auth_token = auth_token

    public_url = ngrok.connect(8000)
    print("Ngrok public URL:", public_url)

    subprocess.call(["python", "manage.py", "runserver", "0.0.0.0:8000"])
