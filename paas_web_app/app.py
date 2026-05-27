from flask import Flask

app = Flask(__name__)


@app.get('/ping')
def ping():
    return 'pong'


def run():
    app.run(host='0.0.0.0', port=8080)
