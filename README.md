# Memorie

Self-hosted photo albums — your photos, your server, your rules. Create albums, upload photos, and share them with friends and family via a share link or a username invite, with a lightweight guest-approval flow for people without accounts.

**No cloud required.** Memorie runs entirely on your own machine or VPS: photos are stored on your local disk and everything is deployable with a single `docker compose up`.

## Features

- **Self-hosted first** — photos live in a plain `media/` folder on *your* disk; your database is a container *you* run. No Cloudinary, no third-party APIs.
- **Albums** — manage photo albums with a UUID primary key and a unique `share_token` for link sharing
- **Photo upload & gallery** — polaroid-style gallery with category filters
- **Lightbox viewer** — full-screen viewing with keyboard navigation
- **Sharing**
  - Share via link (`share_token`)
  - Share via direct username invite (`AlbumShare`)
- **Guest access** — guests view a shared album by entering just their name; the owner approves or declines each guest from the share page
- **Single-owner model** — instances have one owner account; guests and invitees don't need to sign up

## Requirements

- Docker + Docker Compose (recommended)
- Postgres anywhere *you* control (bundled as a container, or point `DATABASE_URL` at your own)

## Quickstart (Docker)

```bash
git clone <repo-url> && cd memorie
cp .env.example .env
# edit .env: set SECRET_KEY, DB_PASSWORD, ADMIN_USERNAME, ADMIN_PASSWORD
docker compose up -d --build
```

Open `http://localhost:8000` and log in with your `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

On first boot the entrypoint runs migrations, collects static files, and creates your owner account (idempotent — it only creates it once).

## Where your data lives / Backups

| What | Where | Back it up with |
|---|---|---|
| Photos | `./media/` on the host | `rsync` / any file backup |
| Database | named volume `pgdata` | `docker compose exec db pg_dump -U memorie memorie > memorie.sql |

Full restore onto a new machine:

```bash
# 1. copy your backup dirs, 2. start fresh stack
docker compose up -d db
cat memorie.sql | docker compose exec -T db psql -U memorie memorie
docker compose up -d web
```

## Serving from a domain

Memorie is stateless — put your normal reverse proxy in front:

**Caddy** (automatic HTTPS):
```
photos.example.com {
    reverse_proxy localhost:8000
}
```

Then set in `.env` and restart:
```
ALLOWED_HOSTS=photos.example.com
CSRF_TRUSTED_HOSTS=photos.example.com
```

## Manual install (no Docker)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # set DATABASE_URL + SECRET_KEY
python manage.py migrate
MEDIA_ROOT=./media python manage.py runserver
```

### Environment Variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret — set a long random string |
| `DEBUG` | `True` only while developing; leave `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hosts the server answers on |
| `CSRF_TRUSTED_HOSTS` | Hosts behind your reverse proxy |
| `DATABASE_URL` | `postgres://memorie:password@db:5432/memorie` (compose sets this for you) |
| `MEDIA_ROOT` | Where photos are stored (compose: `/app/media`) |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_NAME` / `ADMIN_PASSWORD` | Owner account, created on first boot |
| `PORT` | Host port published by compose (default `8000`) |
| `GUNICORN_WORKERS`, `GUNICORN_THREADS` | Optional tuning |

## Data Model

| Model | Purpose |
|---|---|
| `UserProfile` | One-to-one extension of Django's `User` |
| `Album` | UUID primary key, holds a `share_token` for link-based sharing |
| `AlbumShare` | Albums shared directly with a specific user |
| `GuestAccess` | Guest visitors (name only) and their approval status |
| `Image` | Individual photos belonging to an album, stored on local disk |

## Guest Flow

1. A guest opens a shared album link and enters their name — no account needed.
2. A `GuestAccess` record is created in a pending state.
3. The owner approves or declines it from the share page.
4. Approved guests can view the album's photos and lightbox.

## Roadmap Ideas

- Bulk photo upload
- Album cover selection
- Download-all as ZIP
- Thumbnails + EXIF orientation handling
- Client-side encryption (encrypt on upload, decrypt in the browser)

## License

TBD
