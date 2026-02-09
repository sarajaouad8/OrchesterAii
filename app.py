from flask import Flask, request, jsonify, render_template
from config import config
from models import db
from models.user import User

app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize database
db.init_app(app)

@app.route('/')
def home():
    return render_template('cover.html')

@app.route('/cover')
def cover():
    return render_template('cover.html')

@app.route('/login')
def login():
    return render_template('login.html')

# API endpoint to get all users (example)
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint to create a user (example)
@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password')
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
