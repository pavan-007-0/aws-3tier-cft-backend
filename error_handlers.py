"""
Global error handlers and logging configuration
"""
from flask import jsonify, request
import logging
import traceback
import os
from datetime import datetime

# Configure logging
def setup_logging(app):
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure file handler
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.INFO)
    
    # Configure formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Log application startup
    app.logger.info('E-commerce application startup')

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'Bad Request: {request.url} - {error.description}')
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.warning(f'Unauthorized access attempt: {request.url} - IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning(f'Forbidden access attempt: {request.url} - IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f'Resource not found: {request.url}')
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        app.logger.warning(f'Method not allowed: {request.method} {request.url}')
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': f'The {request.method} method is not allowed for this endpoint',
            'status_code': 405
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        app.logger.warning(f'Rate limit exceeded: {request.url} - IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f'Internal Server Error: {request.url} - {str(error)}')
        app.logger.error(f'Traceback: {traceback.format_exc()}')
        
        # In production, don't expose internal error details
        if app.config.get('ENV') == 'production':
            message = 'An internal server error occurred'
        else:
            message = str(error)
        
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': message,
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.error(f'Unexpected error: {request.url} - {str(error)}')
        app.logger.error(f'Traceback: {traceback.format_exc()}')
        
        return jsonify({
            'success': False,
            'error': 'Unexpected Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

def log_request_info(app):
    """Log request information"""
    
    @app.before_request
    def log_request():
        app.logger.info(f'{request.method} {request.url} - IP: {request.remote_addr}')
    
    @app.after_request
    def log_response(response):
        app.logger.info(f'Response: {response.status_code} - {request.method} {request.url}')
        return response

class APIException(Exception):
    """Custom API exception class"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        result = {'success': False, 'message': self.message}
        if self.payload:
            result.update(self.payload)
        return result

def register_api_exception_handler(app):
    """Register handler for custom API exceptions"""
    
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        app.logger.warning(f'API Exception: {error.message} - Status: {error.status_code}')
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response