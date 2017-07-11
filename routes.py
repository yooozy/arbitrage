from flask import Flask
from compare import compare_order_books

app = Flask(__name__)


@app.route('/compare')
def compare():
    compare_order_books()


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World!'


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)
