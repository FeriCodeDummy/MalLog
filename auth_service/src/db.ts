import dotenv from "dotenv";
import mysql, { Pool } from "mysql2/promise";

dotenv.config();

export function createDbPool(): Pool | null {
  const portRaw = process.env.MYSQL_PORT ?? "3306";
  const port = Number.parseInt(portRaw, 10);

  try {
    return mysql.createPool({
      host: process.env.MYSQL_HOST ?? "localhost",
      user: process.env.MYSQL_USER ?? "root",
      password: process.env.MYSQL_PSWD ?? process.env.MYSQL_PASSWORD ?? "",
      database: process.env.MYSQL_DATABASE ?? "auth",
      port: Number.isNaN(port) ? 3306 : port,
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0
    });
  } catch (error) {
    console.error("[!] Failed to create DB pool", error);
    return null;
  }
}
