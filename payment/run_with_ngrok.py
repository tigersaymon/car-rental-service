import os
import subprocess

from pyngrok import conf, ngrok


if __name__ == "__main__":
    auth_token = os.getenv("NGROK_AUTH")
    if auth_token:
        conf.get_default().auth_token = auth_token

    public_url = ngrok.connect(8000)
    print("Ngrok public URL:", public_url)

    subprocess.call(["python", "manage.py", "runserver", "0.0.0.0:8000"])
