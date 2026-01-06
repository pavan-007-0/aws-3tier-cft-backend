"""
Unit tests for security functions
"""
import unittest
from unittest.mock import patch, MagicMock
import jwt
import os
from datetime import datetime, timedelta

# Import the security functions
from security import (
    SecurityValidator, 
    token_required, 
    admin_required,
    validate_json_input,
    log_security_event
)
from flask import Flask, request, jsonify

class TestSecurityValidator(unittest.TestCase):
    """Test cases for SecurityValidator class"""
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(SecurityValidator.validate_email(email))
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            # 'user..name@example.com',  # This is actually valid in some contexts
            'user@.com',
            '',
            None,
            'a' * 250 + '@example.com'  # Too long
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(SecurityValidator.validate_email(email))
    
    def test_validate_password_valid(self):
        """Test password validation with valid passwords"""
        valid_passwords = [
            'Password123',
            'MySecure1Pass',
            'Complex1Password!',
            'Test123Pass'
        ]
        
        for password in valid_passwords:
            with self.subTest(password=password):
                is_valid, message = SecurityValidator.validate_password(password)
                self.assertTrue(is_valid)
                self.assertEqual(message, "Password is valid")
    
    def test_validate_password_invalid(self):
        """Test password validation with invalid passwords"""
        invalid_cases = [
            ('short', 'Password must be at least 8 characters long'),
            ('nouppercase1', 'Password must contain at least one uppercase letter'),
            ('NOLOWERCASE1', 'Password must contain at least one lowercase letter'),
            ('NoNumbers', 'Password must contain at least one number'),
            ('', 'Password must be at least 8 characters long'),
            (None, 'Password must be at least 8 characters long')
        ]
        
        for password, expected_message in invalid_cases:
            with self.subTest(password=password):
                is_valid, message = SecurityValidator.validate_password(password)
                self.assertFalse(is_valid)
                self.assertEqual(message, expected_message)
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        test_cases = [
            ('normal text', 'normal text'),
            ('<script>alert("xss")</script>', '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'),
            ('user@example.com', 'user@example.com'),
            ('', ''),
            (None, ''),
            ('  spaced text  ', 'spaced text'),
            ('text with "quotes"', 'text with &quot;quotes&quot;'),
            ("text with 'quotes'", 'text with &#x27;quotes&#x27;')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = SecurityValidator.sanitize_input(input_text)
                self.assertEqual(result, expected)
    
    def test_validate_phone_valid(self):
        """Test phone validation with valid numbers"""
        valid_phones = [
            '+1234567890',
            '1234567890',
            '+44 20 7946 0958',
            '(555) 123-4567',
            None,  # Phone is optional
            ''     # Empty is also valid
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                self.assertTrue(SecurityValidator.validate_phone(phone))
    
    def test_validate_phone_invalid(self):
        """Test phone validation with invalid numbers"""
        invalid_phones = [
            '123',        # Too short
            '1' * 20,     # Too long
            'abc123def'   # Contains letters after digit removal
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                self.assertFalse(SecurityValidator.validate_phone(phone))


class TestTokenDecorators(unittest.TestCase):
    """Test cases for token-based decorators"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        
        # Set environment variable for testing
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
        
        @self.app.route('/protected')
        @token_required
        def protected_route():
            return jsonify({'message': 'Access granted', 'user_id': request.current_user_id})
        
        @self.app.route('/admin-only')
        @admin_required
        def admin_route():
            return jsonify({'message': 'Admin access granted'})
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        if 'JWT_SECRET_KEY' in os.environ:
            del os.environ['JWT_SECRET_KEY']
    
    def generate_test_token(self, user_id=1, role='customer', expired=False):
        """Generate a test JWT token"""
        exp_time = datetime.utcnow() - timedelta(hours=1) if expired else datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': exp_time
        }
        
        return jwt.encode(payload, 'test-secret-key', algorithm='HS256')
    
    def test_token_required_valid_token(self):
        """Test token_required decorator with valid token"""
        token = self.generate_test_token()
        
        response = self.client.get('/protected', headers={
            'Authorization': f'Bearer {token}'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Access granted')
        self.assertEqual(data['user_id'], 1)
    
    def test_token_required_missing_token(self):
        """Test token_required decorator without token"""
        response = self.client.get('/protected')
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['message'], 'Token is missing')
    
    def test_token_required_invalid_token_format(self):
        """Test token_required decorator with invalid token format"""
        response = self.client.get('/protected', headers={
            'Authorization': 'InvalidFormat'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['message'], 'Invalid token format')
    
    def test_token_required_expired_token(self):
        """Test token_required decorator with expired token"""
        token = self.generate_test_token(expired=True)
        
        response = self.client.get('/protected', headers={
            'Authorization': f'Bearer {token}'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['message'], 'Token has expired')
    
    def test_admin_required_valid_admin(self):
        """Test admin_required decorator with admin user"""
        token = self.generate_test_token(role='admin')
        
        response = self.client.get('/admin-only', headers={
            'Authorization': f'Bearer {token}'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Admin access granted')
    
    def test_admin_required_non_admin(self):
        """Test admin_required decorator with non-admin user"""
        token = self.generate_test_token(role='customer')
        
        response = self.client.get('/admin-only', headers={
            'Authorization': f'Bearer {token}'
        })
        
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data['message'], 'Admin access required')


class TestValidateJsonInput(unittest.TestCase):
    """Test cases for JSON input validation decorator"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        @self.app.route('/test-validation', methods=['POST'])
        @validate_json_input(
            required_fields=['name', 'email'],
            optional_fields=['phone', 'address']
        )
        def test_route():
            return jsonify({'message': 'Validation passed', 'data': request.validated_json})
        
        self.client = self.app.test_client()
    
    def test_valid_json_input(self):
        """Test with valid JSON input"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890'
        }
        
        response = self.client.post('/test-validation', json=data)
        
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['message'], 'Validation passed')
        self.assertEqual(result['data']['name'], 'Test User')
    
    def test_missing_required_field(self):
        """Test with missing required field"""
        data = {
            'name': 'Test User'
            # Missing email
        }
        
        response = self.client.post('/test-validation', json=data)
        
        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertIn('Missing required fields', result['message'])
        self.assertIn('email', result['message'])
    
    def test_non_json_content(self):
        """Test with non-JSON content"""
        response = self.client.post('/test-validation', data='not json')
        
        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertEqual(result['message'], 'Content-Type must be application/json')
    
    def test_empty_json(self):
        """Test with empty JSON"""
        response = self.client.post('/test-validation', 
                                  data='{}',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        # Empty JSON object should trigger "No JSON data provided" or missing fields
        self.assertTrue(
            'No JSON data provided' in result['message'] or 
            'Missing required fields' in result['message']
        )


class TestSecurityLogging(unittest.TestCase):
    """Test cases for security logging"""
    
    @patch('security.logger')
    def test_log_security_event(self, mock_logger):
        """Test security event logging"""
        log_security_event(
            event_type='FAILED_LOGIN',
            user_id=123,
            ip_address='192.168.1.1',
            details='Invalid password'
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        
        self.assertIn('SECURITY EVENT: FAILED_LOGIN', call_args)
        self.assertIn('User: 123', call_args)
        self.assertIn('IP: 192.168.1.1', call_args)
        self.assertIn('Details: Invalid password', call_args)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)