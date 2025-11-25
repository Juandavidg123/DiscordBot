import logging
from flask import Flask
from threading import Thread
from config import Config

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "ok", "message": "Discord bot is running"}

@app.route('/health')
def health():
    return {"status": "healthy"}

def run():
    logger.info(f"Starting web server on {Config.WEBSERVER_HOST}:{Config.WEBSERVER_PORT}")
    app.run(host=Config.WEBSERVER_HOST, port=Config.WEBSERVER_PORT)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()