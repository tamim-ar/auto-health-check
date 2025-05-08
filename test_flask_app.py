from flask import Flask
app = Flask(__name__)

@app.route('/')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(port=5000)
