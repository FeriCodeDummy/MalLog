import dotenv from "dotenv";
import mysql, { Pool } from "mysql2/promise";

dotenv.config();

function readDbConfig() {
  const portRaw = process.env.MYSQL_PORT ?? "3306";
  const port = Number.parseInt(portRaw, 10);

  return {
    host: process.env.MYSQL_HOST ?? "localhost",
    user: process.env.MYSQL_USER ?? "root",
    password: process.env.MYSQL_PSWD ?? process.env.MYSQL_PASSWORD ?? "",
    database: process.env.MYSQL_DATABASE ?? "auth",
    port: Number.isNaN(port) ? 3306 : port,
  };
}

export function createDbPool(): Pool | null {
  const config = readDbConfig();

  try {
    return mysql.createPool({
      host: config.host,
      user: config.user,
      password: config.password,
      database: config.database,
      port: config.port,
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0
    });
  } catch (error) {
    console.error("[!] Failed to create DB pool", error);
    return null;
  }
}

export async function ensureAuthSchema(pool: Pool | null): Promise<void> {
  if (!pool) {
    throw new Error("Database unavailable");
  }

  await pool.execute(`
    CREATE TABLE IF NOT EXISTS User(
      idUser INT PRIMARY KEY AUTO_INCREMENT,
      name VARCHAR(31) NOT NULL,
      surname VARCHAR(31) NOT NULL,
      email VARCHAR(127) NOT NULL UNIQUE,
      password_hash VARCHAR(257) NOT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP()
    );
  `);

  await pool.execute(`
    CREATE TABLE IF NOT EXISTS access_log(
      idLogAccess INT PRIMARY KEY AUTO_INCREMENT,
      fk_account INT DEFAULT NULL,
      ip VARCHAR(127) DEFAULT NULL,
      user_agent VARCHAR(511) DEFAULT NULL,
      email VARCHAR(127) DEFAULT NULL,
      operation VARCHAR(127) NOT NULL DEFAULT 'attempted_login',
      logged_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
      CONSTRAINT fk_access_log_user
        FOREIGN KEY (fk_account) REFERENCES User(idUser)
    );
  `);

  await pool.execute(`
    CREATE TABLE IF NOT EXISTS session(
      idSession INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
      sid VARCHAR(511) NOT NULL UNIQUE,
      ttl DATETIME DEFAULT NULL,
      fk_user INT NOT NULL,
      CONSTRAINT fk_session_user
        FOREIGN KEY (fk_user) REFERENCES User(idUser) ON DELETE CASCADE
    );
  `);
}
