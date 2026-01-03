# Aplicación Web LNB (Flask)

Aplicación web desarrollada con Flask como proyecto académico, basada en la Liga Nacional de Básquet (LNB) de Argentina.

El proyecto consiste en la migración a entorno web de una aplicación de escritorio desarrollada previamente en Java, manteniendo el modelo de dominio y las funcionalidades principales.

---

## Tipo de Aplicación

- Aplicación web clásica
- Backend desarrollado con Flask
- Frontend renderizado del lado del servidor con Jinja
- Estilos responsivos utilizando Tailwind CSS

---

## Arquitectura y Estructura

- Aplicación Flask modular
- Separación clara entre:
  - Punto de entrada y rutas (`app.py`)
  - Modelos de datos (`models.py`)
  - Templates HTML (`templates/`)
  - Recursos estáticos (`static/`)
- Acceso a datos mediante ORM (Flask-SQLAlchemy)
- Autenticación basada en sesiones

---

## Autenticación y Autorización

- Registro e inicio de sesión de usuarios
- Control de acceso por roles
- Autenticación con Google OAuth mediante Authlib
- Encriptación de contraseñas con Flask-Bcrypt
- Gestión de sesiones con Flask-Login

---

## Base de Datos

- Base de datos SQLite
- Administrada mediante SQLAlchemy
- Esquema relacional con claves foráneas
- Base persistente local (`lnb.db`)
- Operaciones CRUD completas para todas las entidades principales

---

## Funcionalidades Principales

- Gestión de usuarios
- Gestión de equipos
- Gestión de jugadores
- Gestión de directores técnicos (DTs)
- Gestión de eventos
- Gestión de artículos
- Interfaces administrativas con control por roles
- Operaciones CRUD completas en todo el sistema

---

## Resumen Automático de Artículos (NLP)

- Generación automática de resúmenes de artículos utilizando Hugging Face Transformers
- Implementación mediante la API `pipeline`
- Funcionalidad implementada a nivel de código
- No testeada completamente en ejecución debido a limitaciones de hardware local
- Feature auxiliar, no central al sistema

---

## Tecnologías Utilizadas

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

## Contexto y Estado del Proyecto

- Proyecto académico individual
- Trabajo final de la materia _Análisis y Metodologías_
- Sistema principal completamente funcional
- Mejoras pendientes:
  - Sistema de progresión y puntos para usuarios
  - Carga de datos reales e imágenes

---

## Idioma

- Versión en español (este archivo)
- English version available here: [README.md](README.md)
