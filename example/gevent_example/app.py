from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello from gevent worker!"


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run()
