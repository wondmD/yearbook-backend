# Yearbook Backend

Django REST Framework backend for the Yearbook application.

## Features

- User authentication with JWT
- User profiles with rich content
- Admin approval system for content creation
- RESTful API endpoints
- File upload support for profile images

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- PostgreSQL (or SQLite for development)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yearbook-backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser_approved
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET /api/auth/me/` - Get current user details
- `GET /api/auth/profile/` - Get or update user profile
- `GET /api/auth/users/` - List all users (admin only)
- `POST /api/auth/users/{id}/approve/` - Approve a user (admin only)

## Project Structure

```
yearbook-backend/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   ├── permissions.py
│   ├── signals.py
│   └── utils.py
└── yearbook/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
This project uses Black for code formatting and isort for import sorting.

```bash
# Auto-format code
black .

# Sort imports
isort .
```

## Deployment

For production deployment, consider using:
- Gunicorn or uWSGI as the application server
- Nginx as the reverse proxy
- PostgreSQL as the database
- Redis for caching (optional)
- Whitenoise for static file serving

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
