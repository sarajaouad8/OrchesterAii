from flask import Blueprint, render_template, session, jsonify, current_app
import requests
from datetime import datetime

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


@main_bp.route('/debug/webhook-test')
def public_webhook_debug():
    """Public debug endpoint to test n8n webhook (no login required)"""
    n8n_url = current_app.config['N8N_WEBHOOK_URL']
    
    try:
        # Test connection to n8n
        response = requests.post(
            n8n_url,
            json={
                'test': 'connection from Flask', 
                'timestamp': str(datetime.now()),
                'source': 'public-debug-endpoint'
            },
            timeout=10
        )
        
        return jsonify({
            'success': True,
            'webhook_url': n8n_url,
            'status_code': response.status_code,
            'response_text': response.text[:500],
            'headers': dict(response.headers)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'webhook_url': n8n_url,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500
