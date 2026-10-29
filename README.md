<div align="center">

# Memorie 📸

**Self-hosted photo albums. Your photos, your server, your rules.**

No cloud. No third-party APIs. No tracking. One command to run.

*Memorie lets you create photo albums and share them with friends & family —
via a share link or a username invite — with a lightweight guest-approval flow
for people who don't have an account. Every photo lives on your own disk,
your database runs on your own machine, and nothing ever leaves your server.*

</div>

---

## Why self-host with Memorie?

Photo-upload apps usually mean uploading your memories to someone else's
computer. Memorie flips that: you run the server, and your photos never leave
hardware you control.

- **Your photos are just files.** Uploads land in a plain `media/` folder on
  your disk. Back them up with `rsync`, copy them to a USB stick, sync them
  however you like — they're yours, in ordinary JPEG/PNG files, not locked
  behind an API.
- **Your database is your database.** A vanilla Postgres container, or point
  `DATABASE_URL` at one you already run.
- **One owner, no social network.** A Memorie instance is for *you*. Friends
  and family are guests — they open your share link, type their name, and you
  approve them. Nobody needs to "sign up for an imagine service."
- **Small.** Django + Postgres in two containers. No Redis, no Celery, no
  message queues, no feature you didn't ask for. It runs comfortably on the
  cheapest VPS or a Raspberry Pi-class box.

## Features

- 🖼️ **Albums** — create, delete, and manage albums; UUID primary keys with a
  regenerable `share_token` for link sharing
- 📤 **Photo upload & gallery** — polaroid-style gallery with category filters
  (family, travel, milestones …) and note search
- 🔍 **Lightbox viewer** — full-screen viewing with keyboard navigation
- 🔗 **Sharing** — via share link or direct username invite (`AlbumShare`)
- 👤 **Guest access** — guests view an album with just a name; the owner
  approves or declines each request from the share page
- 🔒 **Owner-controlled accounts** — no public signups; the instance owner
  creates accounts, and guest links are issue-scoped to a single album
- 🐘 **Plain Postgres + local media** — boring, well-understood plumbing that
  is easy to back up and hard to break

## Quickstart (Docker — recommended)

```bash
git clone https://github.com/devisunknown/memorie.git
cd memorie

cp .env.example .env
$EDITOR .env   # set SECRET_KEY, DB_PASSWORD, ADMIN_USERNAME, ADMIN_PASSWORD

docker compose up -d --build
```

Then open **http://localhost:8000** and log in with your owner credentials.

On first boot the entrypoint does three things for you, in order:

1. applies database migrations,
2. collects static files,
3. creates your owner account — **once** (it is idempotent; restarts skip it).

## Configuration

Everything is configured through `.env` (see `.env.example`); there is no
`config.py` to babysit and no file the app writes back.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret — set it to a long random string |
| `DEBUG` | Leave `False` in production; `True` only when developing |
| `ALLOWED_HOSTS` | Comma-separated hosts the server answers on |
| `CSRF_TRUSTED_HOSTS` | Add your domain here when behind a reverse proxy |
| `DATABASE_URL` | `postgres://memorie:password@db:5432/memorie` (compose sets this) |
| `MEDIA_ROOT` | Where photos live (compose mounts `/app/media` → `./media`) |
| `DB_PASSWORD` | Used by both the app and the bundled Postgres container |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_NAME` / `ADMIN_PASSWORD` | Owner account, created at first boot |
| `PORT` | Host port the web container publishes (default `8000`) |
| `GUNICORN_WORKERS` / `GUNICORN_THREADS` | Web server tuning (defaults `2` / `4`) |

## Serving from a domain

Memorie is stateless — put whatever reverse proxy you already use in front of
it. Nothing about the app dictates your setup.

**Caddy** (automatic HTTPS, two lines):

```
photos.example.com {
    reverse_proxy localhost:8000
}
```

**Nginx**:

```nginx
server {
    listen 443 ssl;
    server_name photos.example.com;

    location / {
        # 100 MB+ so large photo uploads don't get cut off
        client_max_body_size 200M;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then set these in `.env` and restart:

```
ALLOWED_HOSTS=photos.example.com
CSRF_TRUSTED_HOSTS=photos.example.com
```

## Where your data lives — and how to back it up

Everything important is in exactly two places:

| What | Where | Back it up with |
|---|---|---|
| Photos | `./media/` on the host | `rsync`, any file backup tool |
| Database | named volume `pgdata` | `pg_dump` (below) |

Dump the database:

```bash
docker compose exec db pg_dump -U memorie memorie > memorie.sql
```

Restore on a fresh machine:

```bash
# 1. copy ./media/ and memorie.sql over
docker compose up -d db
cat memorie.sql | docker compose exec -T db psql -U memorie memorie
docker compose up -d web
```

That's it — the two commands above (+ your `media/` folder) are the entirety
of a Memorie backup. Test a restore before you need it.

## Manual install (no Docker)

For people who'd rather run their services themselves:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set DATABASE_URL (can point at your own Postgres), SECRET_KEY, etc.

python manage.py migrate
MEDIA_ROOT=./media python manage.py runserver
```

Production without Docker: run gunicorn behind nginx —

```bash
gunicorn oseiantwi.wsgi:application --bind 127.0.0.1:8000 --workers 2
```

## The guest flow

1. The owner opens an album's **Share page** and copies the share link.
2. A visitor opens the link, types their name — no account, no email.
3. That creates a `GuestAccess` record in a *pending* state.
4. The owner approves or declines the request from the Share page.
5. Approved guests see the album and photos. The link can be regenerated at
   any time, which instantly kills all outstanding links.

## Architecture

```
┌──────────────┐        ┌─────────────────────────────┐
│ Your proxy   │        │  web (Django + gunicorn)    │
│ Caddy/Nginx  ├──HTTP──▶│  - app code                 │
└──────────────┘        │  - static via WhiteNoise    │
                        │  - media at /app/media ─────┼───▶ ./media (host disk)
                        └──────────────┬──────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │  db (postgres:16-alpine)    │
                        │  volume: pgdata             │
                        └─────────────────────────────┘
```

- **Django 5** — the whole app (`templates/` is usage-rendered Django, and the
  `memories` app is only a handful of views + models)
- **WhiteNoise** serves static assets, so there is no CDN involved
- **Pillow** for image handling at upload time
- **Postgres 16** — migrations live in `memories/migrations/`

The data model is five models and simple:

| Model | Purpose |
|---|---|
| `UserProfile` | One-to-one extension of Django's `User` |
| `Album` | UUID primary key + regenerable `share_token` |
| `Image` | A photo, stored on local disk |
| `AlbumShare` | Albums shared directly with a named user |
| `GuestAccess` | Guest visitors (name only) + approval status |

## Development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate && python manage.py runserver
```

Code layout:

```
memories/       # the Django app: models, views, urls
oseiantwi/      # project settings
templates/      # all HTML templates
static/         # favicon, …
docker/         # entrypoint.sh for the container
```

## Contributing

PRs are welcome — this is a small project and small PRs are loved. Ideas on
the roadmap if you want one to grab:

- [ ] thumbnails + EXIF orientation fixes
- [ ] bulk upload
- [ ] album cover selection
- [ ] download-all as ZIP
- [ ] client-side encryption (encrypt on upload, decrypt in the browser)

## License

TBD — will be a permissive open-source license (likely MIT).
