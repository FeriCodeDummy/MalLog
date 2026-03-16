from uuid import uuid4


def log(db, action, email=None, user_agent=None, ip=None, account_id=None):
    cursor = db.cursor()
    sql = """
        INSERT INTO access_log (fk_account, ip, user_agent, email, operation)
        VALUES (%s, %s, %s, %s, %s);
    """
    cursor.execute(sql, (account_id, ip, user_agent, email, action))
    db.commit()
    return cursor.lastrowid


def insert_user(db, name, surname, email, password_hash):
    sql = """
        INSERT INTO User(name, surname, email, password_hash)
        VALUES (%s, %s, %s, %s);
    """
    cursor = db.cursor()
    try:
        cursor.execute(sql, (name, surname, email, password_hash))
        db.commit()
    except Exception:
        db.rollback()
        return None

    user_id = cursor.lastrowid
    if not user_id:
        return None

    try:
        log(db, "user_registered", email=email, account_id=user_id)
    except Exception:
        print("failed to log 'user_registered'")

    return user_id


def insert_session(db, uid, email=None):
    cursor = db.cursor()
    session_id = str(uuid4())
    try:
        sql = "INSERT INTO session (sid, fk_user) VALUES (%s, %s);"
        cursor.execute(sql, (session_id, uid))
        db.commit()
    except Exception:
        db.rollback()
        return None

    try:
        log(db, "session_created", email=email, account_id=uid)
    except Exception:
        print("failed to log 'session_created'")

    return session_id


def account_login(db, email, password_hash):
    cursor = db.cursor()
    sql = """
        SELECT idUser, name, surname, email
        FROM User
        WHERE email = %s AND password_hash = %s;
    """
    cursor.execute(sql, (email, password_hash))
    user = cursor.fetchone()

    if not user:
        try:
            log(db, "failed_login", email=email)
        except Exception:
            print("failed to log 'failed_login'")
        return None

    session_id = insert_session(db, user["idUser"], email=user["email"])
    account = {
        "name": user["name"],
        "surname": user["surname"],
        "email": user["email"],
    }
    if session_id:
        account["sessionID"] = session_id

    try:
        log(
            db,
            "login_success",
            email=user["email"],
            account_id=user["idUser"],
        )
    except Exception:
        print("failed to log 'login_success'")

    return account


def fetch_session_data(db, session_id):
    cursor = db.cursor()
    sql = """
        SELECT u.idUser, u.name, u.surname, u.email, s.sid
        FROM session s
        JOIN User u ON u.idUser = s.fk_user
        WHERE s.sid = %s AND (s.ttl IS NULL OR s.ttl > CURRENT_TIMESTAMP)
        LIMIT 1;
    """
    cursor.execute(sql, (session_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return {
        "name": row["name"],
        "surname": row["surname"],
        "email": row["email"],
        "sessionID": row["sid"],
    }


