import { createApp } from "./app";

const app = createApp();
const port = Number.parseInt(process.env.PORT ?? "5000", 10);

app.listen(port, "0.0.0.0", () => {
  console.log(`[+] Express auth service running on 0.0.0.0:${port}`);
});
