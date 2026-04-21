import { createApp } from "./app";
import { createDbPool, ensureAuthSchema } from "./db";

const port = Number.parseInt(process.env.PORT ?? "5000", 10);

async function startServer() {
  const db = createDbPool();
  await ensureAuthSchema(db);

  const app = createApp({ db });
  app.listen(port, "0.0.0.0", () => {
    console.log(`[+] Express auth service running on 0.0.0.0:${port}`);
  });
}

startServer().catch((error) => {
  console.error("[!] Failed to start auth service", error);
  process.exit(1);
});
