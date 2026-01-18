from flask import current_app
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os
from dotenv import load_dotenv

load_dotenv()

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with the app"""
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    mail.init_app(app)

def generate_token(email):
    """Generate a secure token for email verification"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')

def verify_token(token, expiration=3600):
    """Verify the token and return the email if valid"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-verification-salt',
            max_age=expiration
        )
        return email
    except:
        return None

def send_verification_email(user_email):
    """Send verification email to user"""
    token = generate_token(user_email)
    msg = Message(
        'Verify Your Email',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user_email]
    )
    msg.body = f'''To verify your email, visit the following link:
{current_app.config['BASE_URL']}/verify-email/{token}

If you did not make this request then simply ignore this email.
'''
    mail.send(msg)

def send_password_reset_email(user_email):
    """Send password reset email to user"""
    token = generate_token(user_email)
    msg = Message(
        'Password Reset Request',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user_email]
    )
    msg.body = f'''To reset your password, visit the following link:
{current_app.config['BASE_URL']}/reset-password/{token}

If you did not make this request then simply ignore this email.
'''
    mail.send(msg) 