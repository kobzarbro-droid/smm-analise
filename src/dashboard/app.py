"""Flask application factory."""
from flask import Flask
from pathlib import Path


def format_number(num):
    """Format large numbers for display."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Default configuration
    app.config.update(
        SECRET_KEY='dev-secret-key-change-in-production',
        TEMPLATES_AUTO_RELOAD=True,
        JSON_AS_ASCII=False,
        JSON_SORT_KEYS=False,
    )
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Register custom filters
    app.jinja_env.filters['format_number'] = format_number
    
    # Register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app
