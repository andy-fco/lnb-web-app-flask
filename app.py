from flask import Flask, abort, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from datetime import datetime
import requests

from models import (
    db, User, Equipo, Jugador, Articulo, Evento,
    EventoAficionado, AficionadoJugador, DT
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def normalizar_posicion(pos):
    pos = pos.lower()

    if "base" in pos:
        return "Base"
    if "escolta" in pos:
        return "Escolta"
    if "alero" in pos:
        return "Alero"
    if "ala" in pos:
        return "Ala-Pivot"
    if "pivot" in pos:
        return "Pivot"

    return None


app = Flask(__name__)
app.config["SECRET_KEY"] = "clave_secreta_123"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lnb.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
bcrypt = Bcrypt(app)



login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#------------ RUTAS ---------------

#USER-----------------------------------

@app.route("/")
def index():
    articulos = Articulo.query.order_by(Articulo.fecha.desc()).limit(4).all()
    evento_dest = Evento.query.order_by(Evento.fecha_y_hora.asc()).first()
    jugadores = Jugador.query.filter(Jugador.aficionado_id.is_(None)).order_by(Jugador.media.desc()).limit(3).all()


    return render_template(
        "index.html",
        articulos=articulos,
        evento_dest=evento_dest,
        jugadores=jugadores
    )






#EQUIPOS 
@app.route("/equipos")
def equipos():
    all_equipos = Equipo.query.all()
    return render_template("equipos.html", equipos=all_equipos)


@app.route("/equipo/<int:id>")
def equipo_detalle(id):
    equipo = Equipo.query.get_or_404(id)
    jugadores = Jugador.query.filter_by(equipo_id=id).all()
    dts = DT.query.filter_by(equipo_id=id).all()
    return render_template("equipo_detalle.html", equipo=equipo, jugadores=jugadores, dts=dts)

#JUGADORES
@app.route("/jugador/<int:id>")
def jugador_detalle(id):
    jugador = Jugador.query.get_or_404(id)
    return render_template("jugador_detalle.html", jugador=jugador)

#NOVEDADES 

#EVENTSO
@app.route("/eventos")
def eventos():
    lista = Evento.query.order_by(Evento.fecha_y_hora.asc()).all()
    return render_template("eventos.html", eventos=lista)

@app.route("/eventos/<int:id>")
def evento_detalle(id):
    evento = Evento.query.get_or_404(id)
    inscriptos = EventoAficionado.query.filter_by(evento_id=id).count()

    ya_inscripto = False
    if current_user.is_authenticated:
        ya_inscripto = EventoAficionado.query.filter_by(
            evento_id=id,
            aficionado_id=current_user.id
        ).first() is not None

    return render_template("evento_detalle.html",
                           evento=evento,
                           inscriptos=inscriptos,
                           ya_inscripto=ya_inscripto)

@app.route("/eventos/<int:id>/inscribirse")
@login_required
def evento_inscribir(id):
    evento = Evento.query.get_or_404(id)

    inscriptos = EventoAficionado.query.filter_by(evento_id=id).count()
    if inscriptos >= evento.cap_max:
        return "No quedan más cupos."

    ya = EventoAficionado.query.filter_by(
        evento_id=id,
        aficionado_id=current_user.id
    ).first()

    if not ya:
        ins = EventoAficionado(evento_id=id, aficionado_id=current_user.id)
        db.session.add(ins)
        db.session.commit()

    return redirect(url_for("evento_detalle", id=id))

#NOTICIAS
@app.route("/noticias")
def noticias():
    articulos = Articulo.query.order_by(Articulo.fecha.desc()).all()
    return render_template("noticias.html", articulos=articulos)

@app.route("/noticias/<int:id>")
def noticia_detalle(id):
    articulo = Articulo.query.get_or_404(id)
    return render_template("noticia_detalle.html", articulo=articulo)

#JUEGOS

@app.route("/juegos")
@login_required
def juegos():
    return render_template("juegos.html")

#MI JUGADOR

@app.route("/mi_jugador/crear", methods=["GET", "POST"])
@login_required
def crear_mi_jugador():

    
    existente = Jugador.query.filter_by(aficionado_id=current_user.id).first()
    if existente:
        flash("Ya creaste tu jugador. Si querés modificarlo, debés eliminarlo y crearlo de nuevo.", "warning")
        return redirect(url_for("mi_jugador"))

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        ciudad = request.form["ciudad"]
        nacionalidad = request.form["nacionalidad"]
        altura = float(request.form["altura"])
        camiseta = int(request.form["camiseta"])
        posicion = request.form["posicion"]
        mano_habil = request.form["mano_habil"]
        especialidad = request.form["especialidad"]
        jugada = request.form["jugada"]

        stats = {
            "tiro": 65,
            "pase": 65,
            "dribling": 65,
            "velocidad": 65,
            "defensa": 65,
            "salto": 65
        }
 
        bonus_esp = {
            "Tiro": {"tiro": 3, "dribling": 1, "velocidad": 1},
            "Asistencias": {"pase": 3, "dribling": 1, "velocidad": 1},
            "Volcadas": {"salto": 3, "velocidad": 2},
            "Tapas": {"defensa": 3, "salto": 2},
            "Uno contra uno": {"dribling": 3, "velocidad": 2},
            "Defensa": {"defensa": 3, "velocidad": 1, "salto": 1},
            "Poste bajo": {"defensa": 2, "salto": 2},
        }

        if especialidad in bonus_esp:
            for stat, inc in bonus_esp[especialidad].items():
                stats[stat] += inc
 
        bonus_jugada = {
            "Alley-oop": {"pase": 1, "salto": 2},
            "Volcada": {"salto": 2},
            "Volcada en transición": {"velocidad": 2},
            "Triple": {"tiro": 2},
            "Salida de tirador": {"tiro": 2},
            "Stepback": {"tiro": 2, "dribling": 1},
            "Flotadora": {"tiro": 1, "dribling": 1},
            "Gancho": {"tiro": 1, "defensa": 1},
            "Cross-over": {"dribling": 2},
            "Pick n roll": {"pase": 1, "velocidad": 1},
            "Pick n pop": {"tiro": 2},
            "No-look pass": {"pase": 2},
        }

        if jugada in bonus_jugada:
            for stat, inc in bonus_jugada[jugada].items():
                stats[stat] += inc
 
        media = round(sum(stats.values()) / len(stats))
 
        nuevo = Jugador(
            nombre=nombre,
            apellido=apellido,
            ciudad=ciudad,
            nacionalidad=nacionalidad,
            altura=altura,
            camiseta=camiseta,
            posicion=posicion,
            mano_habil=mano_habil,
            especialidad=especialidad,
            jugada=jugada,
            tiro=stats["tiro"],
            pase=stats["pase"],
            dribling=stats["dribling"],
            velocidad=stats["velocidad"],
            defensa=stats["defensa"],
            salto=stats["salto"],
            media=media,
            equipo_id=None,   
            aficionado_id=current_user.id
        )

        db.session.add(nuevo)
        db.session.commit()

        flash("¡Jugador creado con éxito!", "success")
        return redirect(url_for("mi_jugador"))

     
    return render_template("mi_jugador_crear.html")



@app.route("/mi_jugador")
@login_required
def mi_jugador():
    jugador = Jugador.query.filter_by(aficionado_id=current_user.id).first()
    return render_template("mi_jugador.html", jugador=jugador)

# PERFIL
@app.route("/perfil")
@login_required
def perfil():
    user = current_user

    jugador_fav = user.jugador_favorito
    equipo_fav = user.equipo_favorito

    relaciones = (
        AficionadoJugador.query
        .filter_by(aficionado_id=user.id)
        .join(Jugador, AficionadoJugador.jugador_id == Jugador.id)
        .all()
    )

    def posicion_principal(pos):
        if not pos:
            return None
        return pos.split("/")[0].strip()  

    quinteto = {
        "Base": None,
        "Escolta": None,
        "Alero": None,
        "Ala-Pivot": None,
        "Pivot": None,
    }

    for rel in relaciones:
        pos = posicion_principal(rel.jugador.posicion)
        if pos in quinteto:
            quinteto[pos] = rel.jugador

    eventos_inscripto = (
        EventoAficionado.query
        .filter_by(aficionado_id=user.id)
        .join(Evento, EventoAficionado.evento_id == Evento.id)
        .all()
    )

    return render_template(
        "perfil.html",
        user=user,
        jugador_fav=jugador_fav,
        equipo_fav=equipo_fav,
        quinteto=quinteto,
        eventos_inscripto=eventos_inscripto,
    )


@app.route("/perfil/elegir-equipo")
@login_required
def elegir_equipo():
    equipos = Equipo.query.all()
    return render_template("elegir_equipo.html", equipos=equipos)


@app.route("/perfil/guardar-equipo/<int:id>")
@login_required
def guardar_equipo(id):
    equipo = Equipo.query.get_or_404(id)
    current_user.equipo_favorito_id = equipo.id
    db.session.commit()
    flash("Equipo favorito actualizado.", "success")
    return redirect(url_for("perfil"))


@app.route("/perfil/elegir-jugador")
@login_required
def elegir_jugador():
    jugadores = Jugador.query.filter_by(aficionado_id=None).all()
    return render_template("elegir_jugador.html", jugadores=jugadores)


@app.route("/perfil/guardar-jugador/<int:id>")
@login_required
def guardar_jugador(id):
    jugador = Jugador.query.get_or_404(id)
    current_user.jugador_favorito_id = jugador.id
    db.session.commit()
    flash("Jugador favorito actualizado.", "success")
    return redirect(url_for("perfil"))


@app.route("/quinteto/<posicion>")
@login_required
def editar_quinteto(posicion):

    posiciones_validas = ["Base", "Escolta", "Alero", "Ala-Pivot", "Pivot"]
    if posicion not in posiciones_validas:
        abort(404)

    
    def posicion_principal(pos):
        if not pos:
            return None
        return pos.split("/")[0].strip()

    
    jugadores = [
        j for j in Jugador.query.filter_by(aficionado_id=None).all()
        if posicion_principal(j.posicion) == posicion
    ]

    return render_template("quinteto_elegir.html",
                           posicion=posicion,
                           jugadores=jugadores)


@app.route("/quinteto/guardar/<posicion>/<int:jugador_id>")
@login_required
def guardar_quinteto(posicion, jugador_id):

    posiciones_validas = ["Base", "Escolta", "Alero", "Ala-Pivot", "Pivot"]
    if posicion not in posiciones_validas:
        abort(404)

    
    def posicion_principal(pos):
        if not pos:
            return None
        return pos.split("/")[0].strip()

    relaciones = (
        AficionadoJugador.query
        .filter_by(aficionado_id=current_user.id)
        .join(Jugador)
        .all()
    )

    for rel in relaciones:
        if posicion_principal(rel.jugador.posicion) == posicion:
            db.session.delete(rel)

    nueva = AficionadoJugador(
        aficionado_id=current_user.id,
        jugador_id=jugador_id
    )
    db.session.add(nueva)
    db.session.commit()

    flash(f"{posicion} actualizado.", "success")
    return redirect(url_for("perfil"))




@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        mail = request.form["mail"]

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username=username,
            password=hashed_pw,
            mail=mail,
            role="aficionado"
        )

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
            login_user(user)

           
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("index"))

        flash("Credenciales inválidas", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


#ADMIN---------------------------------------

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("index"))
    return render_template("admin/dashboard.html")


#USUARIOS
@app.route("/admin/usuarios")
@login_required
def admin_usuarios():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    q = request.args.get("q", "").strip()

    if q:
        usuarios = User.query.filter(
            (User.username.ilike(f"%{q}%")) |
            (User.mail.ilike(f"%{q}%"))
        ).all()
    else:
        usuarios = User.query.all()

    return render_template("admin/usuarios_list.html", usuarios=usuarios, q=q)

#crear
@app.route("/admin/usuarios/crear", methods=["GET", "POST"])
@login_required
def admin_usuario_crear():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        mail = request.form["mail"]
        password = request.form["password"]
        role = request.form["role"]

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        nuevo = User(
            username=username,
            mail=mail,
            password=hashed,
            role=role
        )
        db.session.add(nuevo)
        db.session.commit()

        return redirect(url_for("admin_usuarios"))

    return render_template("admin/usuario_form.html", modo="crear", usuario=None)


#editar
@app.route("/admin/usuarios/editar/<int:id>", methods=["GET", "POST"])
@login_required
def admin_usuario_editar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    usuario = User.query.get_or_404(id)

    if request.method == "POST":
        usuario.username = request.form["username"]
        usuario.mail = request.form["mail"]
        usuario.role = request.form["role"]

        nueva_pass = request.form.get("password")
        if nueva_pass:
            usuario.password = bcrypt.generate_password_hash(nueva_pass).decode("utf-8")

        db.session.commit()
        return redirect(url_for("admin_usuarios"))

    return render_template("admin/usuario_form.html", modo="editar", usuario=usuario)

#eliminar
@app.route("/admin/usuarios/eliminar/<int:id>")
@login_required
def admin_usuario_eliminar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    usuario = User.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()

    return redirect(url_for("admin_usuarios"))


#EQUIPOS
@app.route("/admin/equipos")
@login_required
def admin_equipos():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    q = request.args.get("q", "")

    if q:
        equipos = Equipo.query.filter(
            (Equipo.nombre.ilike(f"%{q}%")) |
            (Equipo.ciudad.ilike(f"%{q}%"))
        ).all()
    else:
        equipos = Equipo.query.all()

    return render_template("admin/equipos_list.html",
                           equipos=equipos, q=q)

#crear
@app.route("/admin/equipos/crear", methods=["GET", "POST"])
@login_required
def admin_equipo_crear():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":

        fecha_str = request.form["fecha"]  
        fecha = None

        if fecha_str:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        e = Equipo(
            nombre=request.form["nombre"],
            ciudad=request.form["ciudad"],
            estadio=request.form["estadio"],
            fecha_fundacion=fecha,
            temporadas=request.form["temporadas"] or 0,
            campeonatos=request.form["campeonatos"] or 0,
            escudo=request.form["escudo"] or None,
            foto_estadio=request.form["foto_estadio"] or None
        )

        db.session.add(e)
        db.session.commit()

        flash("Equipo creado correctamente.", "success")
        return redirect(url_for("admin_equipos"))

    return render_template("admin/equipos_form.html", equipo=None)

#editar
@app.route("/admin/equipos/<int:id>/editar", methods=["GET", "POST"])
@login_required
def admin_equipo_editar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    equipo = Equipo.query.get_or_404(id)

    if request.method == "POST":
  
        fecha_str = request.form.get("fecha", "")
        fecha = None

        if fecha_str:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
 
        equipo.nombre = request.form["nombre"]
        equipo.ciudad = request.form["ciudad"]
        equipo.estadio = request.form["estadio"]
        equipo.fecha_fundacion = fecha
        equipo.temporadas = request.form["temporadas"] or 0
        equipo.campeonatos = request.form["campeonatos"] or 0
        equipo.escudo = request.form["escudo"] or None
        equipo.foto_estadio = request.form["foto_estadio"] or None

        db.session.commit()
        flash("Equipo actualizado correctamente.", "success")
        return redirect(url_for("admin_equipos"))
 
    return render_template("admin/equipos_form.html", equipo=equipo)


#eliminar
@app.route("/admin/equipos/<int:id>/eliminar")
@login_required
def admin_equipo_eliminar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    equipo = Equipo.query.get_or_404(id)

    db.session.delete(equipo)
    db.session.commit()

    flash("Equipo eliminado correctamente.", "success")
    return redirect(url_for("admin_equipos"))


#JUGADORES---------------------------------
@app.route("/admin/jugadores")
@login_required
def admin_jugadores():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    q = request.args.get("q", "")

    jugadores = Jugador.query.filter(
        Jugador.aficionado_id.is_(None),
        (Jugador.nombre.ilike(f"%{q}%")) | (Jugador.apellido.ilike(f"%{q}%"))
    ).order_by(Jugador.apellido.asc()).all()

    return render_template("admin/jugadores_list.html",
                           jugadores=jugadores,
                           q=q)

#crear
from datetime import datetime

@app.route("/admin/jugadores/crear", methods=["GET", "POST"])
@login_required
def admin_jugador_crear():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    equipos = Equipo.query.order_by(Equipo.nombre.asc()).all()

    if request.method == "POST":

         
        fecha_str = request.form.get("fecha_nacimiento")
        fecha_nac = None
        if fecha_str:
            try:
                fecha_nac = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except:
                fecha_nac = None   

        equipo_id = request.form.get("equipo_id") or None

        j = Jugador(
            nombre=request.form["nombre"],
            apellido=request.form["apellido"],
            camiseta=int(request.form["camiseta"] or 0),
            media=int(request.form["media"] or 0),
            posicion=request.form["posicion"],
            nacionalidad=request.form["nacionalidad"],
            equipo_id=equipo_id,

            tiro=int(request.form["tiro"] or 0),
            dribling=int(request.form["dribling"] or 0),
            velocidad=int(request.form["velocidad"] or 0),
            pase=int(request.form["pase"] or 0),
            defensa=int(request.form["defensa"] or 0),
            salto=int(request.form["salto"] or 0),

            fecha_nacimiento=fecha_nac,
            ciudad=request.form["ciudad"] or None,
            altura=float(request.form["altura"] or 0) if request.form["altura"] else None,
            mano_habil=request.form["mano_habil"] or None,
            especialidad=request.form["especialidad"] or None,
            jugada=request.form["jugada"] or None,

            aficionado_id=None,
            foto_carnet=request.form["foto_carnet"] or None,
            media_day=request.form["media_day"] or None,
            foto_juego=request.form["foto_juego"] or None,
        )

        db.session.add(j)
        db.session.commit()

        flash("Jugador creado correctamente.", "success")
        return redirect(url_for("admin_jugadores"))

    return render_template("admin/jugadores_form.html",
                           jugador=None,
                           equipos=equipos)

#editar
@app.route("/admin/jugadores/<int:id>/editar", methods=["GET", "POST"])
@login_required
def admin_jugador_editar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    jugador = Jugador.query.get_or_404(id)

    if jugador.aficionado_id is not None:
        flash("No podés editar jugadores creados por usuarios.", "danger")
        return redirect(url_for("admin_jugadores"))

    equipos = Equipo.query.order_by(Equipo.nombre.asc()).all()

    if request.method == "POST":

        
        fecha_str = request.form.get("fecha_nacimiento")
        fecha_nac = None
        if fecha_str:
            try:
                fecha_nac = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except:
                fecha_nac = None

        equipo_id = request.form.get("equipo_id") or None

        jugador.nombre = request.form["nombre"]
        jugador.apellido = request.form["apellido"]
        jugador.camiseta = int(request.form["camiseta"] or 0)
        jugador.media = int(request.form["media"] or 0)
        jugador.posicion = request.form["posicion"]
        jugador.nacionalidad = request.form["nacionalidad"]
        jugador.equipo_id = equipo_id

        jugador.tiro = int(request.form["tiro"] or 0)
        jugador.dribling = int(request.form["dribling"] or 0)
        jugador.velocidad = int(request.form["velocidad"] or 0)
        jugador.pase = int(request.form["pase"] or 0)
        jugador.defensa = int(request.form["defensa"] or 0)
        jugador.salto = int(request.form["salto"] or 0)

        jugador.fecha_nacimiento = fecha_nac
        jugador.ciudad = request.form["ciudad"] or None
        jugador.altura = float(request.form["altura"] or 0) if request.form["altura"] else None
        jugador.mano_habil = request.form["mano_habil"] or None
        jugador.especialidad = request.form["especialidad"] or None
        jugador.jugada = request.form["jugada"] or None

        jugador.foto_carnet = request.form["foto_carnet"] or None
        jugador.media_day = request.form["media_day"] or None
        jugador.foto_juego = request.form["foto_juego"] or None

        db.session.commit()

        flash("Jugador actualizado correctamente.", "success")
        return redirect(url_for("admin_jugadores"))

    return render_template("admin/jugadores_form.html",
                           jugador=jugador,
                           equipos=equipos)


#eliminar
@app.route("/admin/jugadores/<int:id>/eliminar")
@login_required
def admin_jugador_eliminar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    jugador = Jugador.query.get_or_404(id)

    if jugador.aficionado_id is not None:
        flash("No podés eliminar jugadores creados por aficionados.", "danger")
        return redirect(url_for("admin_jugadores"))

    db.session.delete(jugador)
    db.session.commit()

    flash("Jugador eliminado.", "success")
    return redirect(url_for("admin_jugadores"))








#ARTICULOS------------------------------
@app.route("/admin/articulos")
@login_required
def admin_articulos():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    q = request.args.get("q", "").strip()

    if q:
        articulos = Articulo.query.filter(
            Articulo.titulo.ilike(f"%{q}%")|
            Articulo.descripcion.ilike(f"%{q}%")
        ).all()
    else:
        articulos = Articulo.query.all()

    return render_template("admin/articulos_list.html", articulos=articulos, q=q)

#crear
@app.route("/admin/articulos/crear", methods=["GET", "POST"])
@login_required
def admin_articulos_crear():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        a = Articulo(
            titulo=request.form["titulo"],
            descripcion=request.form["descripcion"],
            fecha=datetime.now().date(),      
            portada=request.form["portada"] or None,
            foto_1=request.form["foto_1"] or None,
            foto_2=request.form["foto_2"] or None,
            foto_3=request.form["foto_3"] or None
        )

        db.session.add(a)
        db.session.commit()
        flash("Artículo creado correctamente.", "success")
        return redirect(url_for("admin_articulos"))

    return render_template("admin/articulos_form.html", articulo=None)

#editar
@app.route("/admin/articulos/<int:id>/editar", methods=["GET", "POST"])
@login_required
def admin_articulos_editar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    articulo = Articulo.query.get_or_404(id)

    if request.method == "POST":
        articulo.titulo = request.form["titulo"]
        articulo.descripcion = request.form["descripcion"]
        articulo.portada = request.form["portada"] or None
        articulo.foto_1 = request.form["foto_1"] or None
        articulo.foto_2 = request.form["foto_2"] or None
        articulo.foto_3 = request.form["foto_3"] or None

        db.session.commit()
        flash("Artículo actualizado.", "success")
        return redirect(url_for("admin_articulos"))

    return render_template("admin/articulos_form.html", articulo=articulo)

#eliminar
@app.route("/admin/articulos/<int:id>/eliminar")
@login_required
def admin_articulos_eliminar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    articulo = Articulo.query.get_or_404(id)

    db.session.delete(articulo)
    db.session.commit()

    flash("Artículo eliminado correctamente.", "success")
    return redirect(url_for("admin_articulos"))


#EVENTOS--------------------------------
@app.route("/admin/eventos")
@login_required
def admin_eventos():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    q = request.args.get("q", "")

    if q:
        eventos = Evento.query.filter(Evento.titulo.ilike(f"%{q}%")).all()
    else:
        eventos = Evento.query.order_by(Evento.fecha_y_hora.desc()).all()

    return render_template("admin/eventos_list.html", eventos=eventos, q=q)

#crear
@app.route("/admin/eventos/crear", methods=["GET", "POST"])
@login_required
def admin_eventos_crear():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        fecha_raw = request.form["fecha_y_hora"]
        fecha = datetime.strptime(fecha_raw, "%Y-%m-%dT%H:%M")

        e = Evento(
            titulo=request.form["titulo"],
            descripcion=request.form["descripcion"],
            fecha_y_hora=fecha,
            cap_max=request.form["cap_max"],
            portada=request.form["portada"] or None,
            foto_1=request.form["foto_1"] or None,
        )

        db.session.add(e)
        db.session.commit()

        flash("Evento creado correctamente.", "success")
        return redirect(url_for("admin_eventos"))

    return render_template("admin/eventos_form.html", evento=None)


#editar
@app.route("/admin/eventos/<int:id>/editar", methods=["GET", "POST"])
@login_required
def admin_eventos_editar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    evento = Evento.query.get_or_404(id)

    if request.method == "POST":
        fecha_raw = request.form["fecha_y_hora"]
        fecha = datetime.strptime(fecha_raw, "%Y-%m-%dT%H:%M")

        evento.titulo = request.form["titulo"]
        evento.descripcion = request.form["descripcion"]
        evento.fecha_y_hora = fecha
        evento.cap_max = request.form["cap_max"]
        evento.portada = request.form["portada"] or None
        evento.foto_1 = request.form["foto_1"] or None

        db.session.commit()

        flash("Evento actualizado correctamente.", "success")
        return redirect(url_for("admin_eventos"))

    return render_template("admin/eventos_form.html", evento=evento)


#eliminar
@app.route("/admin/eventos/<int:id>/eliminar")
@login_required
def admin_eventos_eliminar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    evento = Evento.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()

    flash("Evento eliminado.", "success")
    return redirect(url_for("admin_eventos"))



#DTS------------------------------
@app.route("/admin/dts")
@login_required
def admin_dts():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    q = request.args.get("q", "").strip()

    if q:
        dts = DT.query.filter(
            (DT.nombre.ilike(f"%{q}%")) |
            (DT.apellido.ilike(f"%{q}%")) 
        ).all()
    else:
        dts = DT.query.all()

    return render_template("admin/dts_list.html", dts=dts, q=q)

#crear
@app.route("/admin/dts/crear", methods=["GET", "POST"])
@login_required
def admin_dts_crear():
    if current_user.role != "admin":
        return redirect(url_for("index"))

    equipos = Equipo.query.all()

    if request.method == "POST":
        fecha_str = request.form["fecha_nacimiento"]
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None

        dt = DT(
            nombre=request.form["nombre"],
            apellido=request.form["apellido"],
            fecha_nacimiento=fecha,
            nacionalidad=request.form["nacionalidad"],
            ciudad=request.form["ciudad"],
            equipo_id=request.form["equipo_id"] or None,
            temporadas=request.form["temporadas"],
            foto=request.form["foto"] or None
        )

        db.session.add(dt)
        db.session.commit()
        flash("DT creado correctamente.", "success")
        return redirect(url_for("admin_dts"))

    return render_template("admin/dts_form.html", dt=None, equipos=equipos)

#editar
@app.route("/admin/dts/<int:id>/editar", methods=["GET", "POST"])
@login_required
def admin_dts_editar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    dt = DT.query.get_or_404(id)
    equipos = Equipo.query.all()

    if request.method == "POST":
        fecha_str = request.form["fecha_nacimiento"]
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None

        dt.nombre = request.form["nombre"]
        dt.apellido = request.form["apellido"]
        dt.fecha_nacimiento = fecha
        dt.nacionalidad = request.form["nacionalidad"]
        dt.ciudad = request.form["ciudad"]
        dt.equipo_id = request.form["equipo_id"] or None
        dt.temporadas = request.form["temporadas"]
        dt.foto = request.form["foto"] or None

        db.session.commit()
        flash("DT actualizado correctamente.", "success")
        return redirect(url_for("admin_dts"))

    return render_template("admin/dts_form.html", dt=dt, equipos=equipos)

#eliminar
@app.route("/admin/dts/<int:id>/eliminar")
@login_required
def admin_dts_eliminar(id):
    if current_user.role != "admin":
        return redirect(url_for("index"))

    dt = DT.query.get_or_404(id)
    db.session.delete(dt)
    db.session.commit()
    flash("DT eliminado correctamente.", "success")
    return redirect(url_for("admin_dts"))


# --------- INICIALIZAR ---------

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
