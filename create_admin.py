from app import app, db, User, bcrypt

with app.app_context():
    hashed = bcrypt.generate_password_hash("1234").decode("utf-8")

    admin = User(
        username="admin",
        password=hashed,
        mail="admin@lnb.com",
        role="admin"
    )

    db.session.add(admin)
    db.session.commit()

    print("✔ Admin creado con éxito")
