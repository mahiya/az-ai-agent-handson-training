from flask import Flask
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)


@app.route("/api/sample", methods=["GET"])
def sample_api():
    return "Hello, World!", 200


if __name__ == "__main__":
    app.run()
