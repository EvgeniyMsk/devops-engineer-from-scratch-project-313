import sentry_sdk
from flask import Flask

sentry_sdk.init(
    dsn="https://b3aa1c5286c4f95856f7bb623b02dc14@o4511463773765632.ingest.de.sentry.io/4511466076110928",
    send_default_pii=True,
)


app = Flask(__name__)


@app.get('/ping')
def ping():
    return 'pong'


def run():
    app.run(host='0.0.0.0', port=8080)
