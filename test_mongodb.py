from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

@app.route('/')
def health_check():
    try:
        # Try to connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        # Force a connection attempt
        client.admin.command('ping')
        return {'status': 'healthy', 'message': 'MongoDB is running'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 503

if __name__ == '__main__':
    app.run(port=27017)
