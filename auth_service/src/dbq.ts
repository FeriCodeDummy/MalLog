import { ResultSetHeader, RowDataPacket } from "mysql2/promise";
import { v4 as uuidv4 } from "uuid";

import { AccountResponse } from "./types";

interface DbExecutor {
  execute<T extends ResultSetHeader | RowDataPacket[]>(
    sql: string,
    values?: unknown[]
  ): Promise<[T, unknown]>;
}

interface UserRow extends RowDataPacket {
  idUser: number;
  name: string;
  surname: string;
  email: string;
}

interface SessionRow extends RowDataPacket {
  idUser: number;
  name: string;
  surname: string;
  email: string;
  sid: string;
}

export async function log(
  db: DbExecutor,
  action: string,
  email?: string,
  userAgent?: string,
  ip?: string,
  accountId?: number
): Promise<number | null> {
  try {
    const sql = `
      INSERT INTO access_log (fk_account, ip, user_agent, email, operation)
      VALUES (?, ?, ?, ?, ?);
    `;
    const [result] = await db.execute<ResultSetHeader>(sql, [
      accountId ?? null,
      ip ?? null,
      userAgent ?? null,
      email ?? null,
      action
    ]);
    return result.insertId;
  } catch (error) {
    console.error("failed to write access log", error);
    return null;
  }
}

export async function insertUser(
  db: DbExecutor,
  name: string,
  surname: string,
  email: string,
  passwordHash: string
): Promise<number | null> {
  const sql = `
    INSERT INTO User(name, surname, email, password_hash)
    VALUES (?, ?, ?, ?);
  `;

  try {
    const [result] = await db.execute<ResultSetHeader>(sql, [name, surname, email, passwordHash]);
    await log(db, "user_registered", email, undefined, undefined, result.insertId);
    return result.insertId;
  } catch (error) {
    console.error("failed to insert user", error);
    return null;
  }
}

export async function insertSession(
  db: DbExecutor,
  userId: number,
  email?: string
): Promise<string | null> {
  const sessionId = uuidv4();
  const sql = "INSERT INTO session (sid, fk_user) VALUES (?, ?);";

  try {
    await db.execute<ResultSetHeader>(sql, [sessionId, userId]);
    await log(db, "session_created", email, undefined, undefined, userId);
    return sessionId;
  } catch (error) {
    console.error("failed to create session", error);
    return null;
  }
}

export async function accountLogin(
  db: DbExecutor,
  email: string,
  passwordHash: string
): Promise<AccountResponse | null> {
  const sql = `
    SELECT idUser, name, surname, email
    FROM User
    WHERE email = ? AND password_hash = ?;
  `;

  const [rows] = await db.execute<UserRow[]>(sql, [email, passwordHash]);
  const user = rows[0];

  if (!user) {
    await log(db, "failed_login", email);
    return null;
  }

  const sessionId = await insertSession(db, user.idUser, user.email);
  await log(db, "login_success", user.email, undefined, undefined, user.idUser);

  return {
    name: user.name,
    surname: user.surname,
    email: user.email,
    sessionID: sessionId
  };
}

export async function fetchSessionData(
  db: DbExecutor,
  sessionId: string
): Promise<AccountResponse | null> {
  const sql = `
    SELECT u.idUser, u.name, u.surname, u.email, s.sid
    FROM session s
    JOIN User u ON u.idUser = s.fk_user
    WHERE s.sid = ? AND (s.ttl IS NULL OR s.ttl > CURRENT_TIMESTAMP)
    LIMIT 1;
  `;

  const [rows] = await db.execute<SessionRow[]>(sql, [sessionId]);
  const row = rows[0];
  if (!row) {
    return null;
  }

  return {
    name: row.name,
    surname: row.surname,
    email: row.email,
    sessionID: row.sid
  };
}
