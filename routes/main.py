from flask import Blueprint, render_template, session, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return render_template('cover.html')


@main_bp.route('/test-session')
def test_session():
    """Test if sessions work at all."""
    # Set a test value
    session['test'] = 'Session is working!'
    session['counter'] = session.get('counter', 0) + 1
    return jsonify({
        'message': 'Session set successfully',
        'session_data': dict(session)
    })


@main_bp.route('/debug-session')
def debug_session():
    """Debug route to view session contents."""
    return jsonify({
        'session': dict(session),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    })
