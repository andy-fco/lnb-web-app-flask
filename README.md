# LNB Web Application (Flask)

Web application developed with Flask as an academic project, based on the Argentine National Basketball League (Liga Nacional de Básquet – LNB).

This project represents a web-based migration of a previous Java desktop application, maintaining the same domain model and core functionalities while adapting them to a modern web environment.

---

## Application Type

- Classical web application
- Backend built with Flask
- Server-side rendered frontend using Jinja templates
- Responsive styling with Tailwind CSS

---

## Architecture and Structure

- Modular Flask application
- Clear separation between:
  - Application entry point and routing (`app.py`)
  - Data models (`models.py`)
  - HTML templates (`templates/`)
  - Static assets (`static/`)
- ORM-based data access using Flask-SQLAlchemy
- Session-based authentication

---

## Authentication and Authorization

- User registration and login
- Role-based access control
- Google OAuth authentication using Authlib
- Password hashing with Flask-Bcrypt
- User session management with Flask-Login

---

## Database

- SQLite database
- Managed through SQLAlchemy ORM
- Relational schema with foreign keys
- Persistent local database (`lnb.db`)
- Complete CRUD operations for all main entities

---

## Main Features

- User management
- Team management
- Player management
- Coaches (DTs) management
- Events management
- Articles management
- Role-based administrative interfaces
- Fully functional CRUD operations across the system

---

## NLP-Based Article Summarization

- Automatic article summarization implemented using Hugging Face Transformers
- Text summarization handled via the `pipeline` API
- Feature implemented at code level but not fully tested in execution due to local hardware limitations
- Designed as an auxiliary feature, not a core dependency of the system

---

## Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- Authlib (Google OAuth)
- Jinja2
- Tailwind CSS
- SQLite
- Hugging Face Transformers

---

## Project Context and Status

- Individual academic project
- Final project for the course _Análisis y Metodologías_
- Core system fully functional
- Pending improvements:
  - User progression and points system
  - Enrichment of content with real-world data and images

---

## Language

- English version (this file)
- Spanish version available here: [README.es.md](README.es.md)
