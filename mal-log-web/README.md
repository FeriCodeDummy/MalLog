# MalLog Web

Dark minimal Next.js UI for LOG upload and gateway-triggered analysis.

## Features

- Upload `.log` from the browser
- Calls Next.js server route `POST /api/analyze`
- Server route validates file and calls API gateway `POST /submit`
- Displays processed/success/failed counters and anomaly responses in JSON

## Configuration

Set one of these environment variables for gateway target:

- `API_GATEWAY_URL` (server-side preferred)
- `NEXT_PUBLIC_API_GATEWAY_URL` (fallback)

Default is `http://localhost:18080`.

## Local run

```bash
npm run dev
```
