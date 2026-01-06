#!/usr/bin/env python3
"""
Installation script for backend dependencies and security setup
"""
import subprocess
import sys
import os
import secrets
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def generate_secure_keys():
    """Generate secure keys for the application"""
    print("🔐 Generating secure keys...")
    
    secret_key = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(32)
    password_salt = secrets.token_urlsafe(16)
    
    return secret_key, jwt_secret, password_salt

def update_env_file():
    """Update .env file with secure keys"""
    print("📝 Updating .env file with secure keys...")
    
    secret_key, jwt_secret, password_salt = generate_secure_keys()
    
    env_content = f"""# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=22H71A6101
DB_NAME=ecommerce_db

# Security Configuration (CHANGE THESE IN PRODUCTION!)
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Security Headers
SECURITY_PASSWORD_SALT={password_salt}

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://

# CORS Origins (Update for production)
CORS_ORIGINS=http://localhost:4200,https://yourdomain.com
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file updated with secure keys")
    print("⚠️  IMPORTANT: Change these keys in production!")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        run_command('python -m venv venv', 'Creating virtual environment')
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate && '
    else:  # Unix/Linux/Mac
        activate_cmd = 'source venv/bin/activate && '
    
    run_command(f'{activate_cmd}pip install --upgrade pip', 'Upgrading pip')
    run_command(f'{activate_cmd}pip install -r requirements.txt', 'Installing dependencies')

def create_logs_directory():
    """Create logs directory for application logging"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")

def setup_database():
    """Setup database tables"""
    print("🗄️  Setting up database...")
    
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate && '
    else:  # Unix/Linux/Mac
        activate_cmd = 'source venv/bin/activate && '
    
    run_command(f'{activate_cmd}python create_tables.py', 'Creating database tables')

def main():
    """Main installation function"""
    print("🚀 Starting E-commerce Backend Security Setup")
    print("=" * 50)
    
    # Check if Python is available
    try:
        python_version = subprocess.check_output([sys.executable, '--version'], text=True)
        print(f"✅ Python found: {python_version.strip()}")
    except:
        print("❌ Python not found. Please install Python 3.8+")
        return
    
    # Install dependencies
    install_dependencies()
    
    # Update environment file
    update_env_file()
    
    # Create necessary directories
    create_logs_directory()
    
    # Setup database
    setup_database()
    
    print("\n" + "=" * 50)
    print("🎉 Security setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Review and update the .env file with your production values")
    print("2. Configure your MySQL database connection")
    print("3. Set up HTTPS/TLS certificates for production")
    print("4. Configure your firewall and security groups")
    print("5. Run the application: python app.py")
    print("\n⚠️  Security reminders:")
    print("- Change all default passwords and keys")
    print("- Enable HTTPS in production")
    print("- Set up proper database backups")
    print("- Configure monitoring and alerting")
    print("- Review and test all security measures")

if __name__ == "__main__":
    main()