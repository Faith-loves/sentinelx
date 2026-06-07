# Separate Deploy

## Render backend

Deploy from the repo root using `render.yaml`.

Set this Render env var after your Vercel frontend URL is ready:

```txt
SENTINELX_CORS_ORIGINS=https://your-frontend.vercel.app
```

Also set:

```txt
SENTINELX_ADMIN_EMAIL=your@email.com
SENTINELX_ADMIN_PASSWORD=your-strong-password
```

Backend URL will look like:

```txt
https://sentinelx-backend.onrender.com
```

## Vercel frontend

Import the same repo into Vercel and set Root Directory to:

```txt
frontend
```

Set this Vercel env var:

```txt
NEXT_PUBLIC_API_URL=https://sentinelx-backend.onrender.com
```

Then redeploy frontend.
