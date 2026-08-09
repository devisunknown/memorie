
# memorie
# Memorie

A photo album sharing app built with Django, Tailwind CSS, and Cloudinary. Create albums, upload photos, and share them with friends and family — either via a shareable link or a direct username invite, with a lightweight guest-approval flow for non-account visitors.

## Features

- **Albums** — create and manage photo albums with a UUID-based primary key and a unique `share_token` for link sharing
- **Photo upload & gallery** — upload photos into a polaroid-style gallery with category filters
- **Lightbox viewer** — full-screen image viewing with keyboard navigation (arrow keys to move between photos)
- **Sharing**
  - Share via link (`share_token`)
  - Share via direct username invite (`AlbumShare`)
- **Guest access** — guests can view a shared album by entering just their name (no account required); the album owner approves or declines each guest from the share page
- **User profiles** — extended user data via a one-to-one `UserProfile`

## Tech Stack

- **Backend:** Django
- **Styling:** Tailwind CSS
- **Media storage:** Cloudinary
- **Database:** PostgreSQL (recommended for production)

## Data Model

| Model | Purpose |
|---|---|
| `UserProfile` | One-to-one extension of Django's `User` |
| `Album` | UUID primary key, holds a `share_token` for link-based sharing |
| `AlbumShare` | Tracks albums shared directly with a specific user |
| `GuestAccess` | Tracks guest visitors (name only) and their approval status |
| `Image` | Individual photos belonging to an album, stored via Cloudinary |

## Guest Flow

1. A guest opens a shared album link and enters their name — no sign-up required.
2. A `GuestAccess` record is created in a pending state.
3. The album owner sees the request on the share page and approves or declines it.
4. Approved guests can view the album's photo gallery and lightbox.

## Getting Started

```bash
# clone the repo
git clone <repo-url>
cd memorie

# create a virtual environment
python -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# configure environment variables (Cloudinary, database, secret key)
cp .env.example .env

# run migrations
python manage.py migrate

# start the dev server
python manage.py runserver
```

### Environment Variables

```
SECRET_KEY=
DEBUG=True
DATABASE_URL=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

## Roadmap Ideas

- Bulk photo upload
- Album cover selection
- Download-all as ZIP
- Email notifications for guest requests

## License

TBD


