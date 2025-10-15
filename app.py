
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "clave_secreta_123" 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirige al login si intenta entrar sin auth


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        rol = request.form["rol"]
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, password=hashed_pw , rol = rol)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)  # Crea la sesión
            return redirect(url_for("protected"))
        else:
            return "Credenciales inválidas"

    return render_template('login.html')


@app.route("/admin")
@login_required
def admin():
    return render_template('admin.html' , usuario = current_user.username , usuarios = User.query.all())
@app.route("/protected")
@login_required
def protected():
    if current_user.rol == "admin":
        return redirect('admin')
    return render_template("protected.html" , usuaario= current_user.username)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
@app.route("/clima", methods=["GET", "POST"])
@login_required
def clima():
    weather_data = None
    if request.method == "POST":
        ciudad = request.form["ciudad"]
        api_key = "f56823a092569c386960376448523823"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
        else:
            weather_data = {"error": "No se pudo obtener el clima"}

    return render_template("clima.html", weather=weather_data)
@app.route("/Usuarios", methods=["GET","POST"])
@login_required
def usuarios():
    Users_data = None
    if request.method =="POST":
        id_user = request.form["id"]
        url = f"https://api.escuelajs.co/api/v1/users/{int(id_user)}"
        response = requests.get(url)
        if response.status_code == 200:
            Users_data = response.json()
        else:
            Users_data = {"error": "No se pudo obtener el usuario"}

    return render_template("usuarios.html", Users=Users_data)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
