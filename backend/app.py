from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import openai
from datetime import datetime
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from redis import Redis
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'd49af2116cc63cf19afa9da7a1c5879c'
app.config['SESSION_COOKIE_SECURE'] = True  # Secure cookies
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Initialize Redis and Limiter with Redis storage
redis = Redis(host='localhost', port=6379, db=0)  # Adjust settings as needed
limiter = Limiter(
    get_remote_address,  # Use remote address as key function
    app=app,
    storage_uri='redis://localhost:6379/0',  # Redis URI
    default_limits=["200 per day", "50 per hour"]  # Set default rate limits
)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# OpenAI API key
openai.api_key = 'sk-N93Tc9xg4X4jknMAkoH0HUcb5stTjzEZ_7Xy4XxpzGT3BlbkFJVtydRXv7TvkM-lwuFFgFPVj1GJpVlds19nkAAA7sgA'

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    queries = db.relationship('Query', order_by='Query.timestamp', back_populates='user')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Define the Query model
class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    query_text = db.Column(db.String(500), nullable=False)
    response_text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='queries')

# Initialize the database within the application context
with app.app_context():
    db.create_all()

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting for registration
def register():
    data = request.json
    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    new_user = User(name=data['name'], email=data['email'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting for login
def login():
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/reset_password', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting for password reset
def reset_password():
    data = request.json
    if not data.get('email') or not data.get('new_password'):
        return jsonify({'message': 'Missing required fields'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if user:
        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    return jsonify({'message': 'User not found'}), 404

@app.route('/update_profile', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting for profile updates
def update_profile():
    if 'user_id' not in session:
        return jsonify({'message': 'Not logged in'}), 401

    data = request.json
    user = User.query.get(session['user_id'])
    if data.get('name'):
        user.name = data['name']
    if data.get('email'):
        user.email = data['email']
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/ask', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting for queries
def ask():
    user_input = request.json.get('query')
    if not user_input:
        return jsonify({'message': 'No query provided'}), 400
    response = process_query(user_input)
    if 'user_id' in session:
        new_query = Query(user_id=session['user_id'], query_text=user_input, response_text=response)
        db.session.add(new_query)
        db.session.commit()
    return jsonify({'response': response})

@app.route('/history', methods=['GET'])
@limiter.limit("10 per minute")  # Rate limiting for history retrieval
def history():
    if 'user_id' not in session:
        return jsonify({'message': 'Not logged in'}), 401

    user_id = session['user_id']
    queries = Query.query.filter_by(user_id=user_id).order_by(Query.timestamp.desc()).all()
    history = [{'query': q.query_text, 'response': q.response_text, 'timestamp': q.timestamp} for q in queries]
    
    return jsonify(history)

def process_query(query):
    # Call OpenAI API
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # or "gpt-3.5-turbo" for GPT-3.5
            prompt=query,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logging.error(f"OpenAI API call failed: {e}")
        return "An error occurred while processing your query."

if __name__ == '__main__':
    app.run(debug=True)
