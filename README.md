# freud, maslow & beyond

An independent educational publishing platform about psychology, motivation and human behaviour.
Built with Django and Bootstrap (Clean Blog theme), served with WhiteNoise, intended for deployment
on Render with PostgreSQL.

**Mission:** Make the study of human behaviour easier to explore without making it simplistic.

## Stack

- Django 5.2 · Bootstrap 5 · WhiteNoise (static files) · Gunicorn
- SQLite for local development; PostgreSQL in production via `DATABASE_URL`
- Pillow (images); Django's built-in sitemaps for `sitemap.xml`

## Local development

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Create an editor account and start writing:

```bash
python manage.py createsuperuser
# then open /admin/ → Posts → New post
```

## Tests and checks

```bash
python manage.py check
python manage.py test
```

The test suite covers the core reading journey: home, article listing and pagination,
article detail (published-only, correct 404s), the legacy `/post/<id>/` redirect,
the contact form, newsletter sign-up, sitemap and robots.txt.

## Environment variables

Development works with no environment variables (`DEBUG=True` by default).
**Production requires `DEBUG=False`, `SECRET_KEY` and `ALLOWED_HOSTS`** — the app
refuses to start in production without them.

| Variable | Required in prod | Purpose |
| --- | --- | --- |
| `DEBUG` | yes | `False` in production |
| `SECRET_KEY` | yes | Django secret key |
| `ALLOWED_HOSTS` | yes | Comma-separated hostnames |
| `CSRF_TRUSTED_ORIGINS` | recommended | Comma-separated origins, e.g. `https://your-site.onrender.com` |
| `DATABASE_URL` | yes (Render provides) | PostgreSQL connection string |
| `DB_SSLMODE` | no | PostgreSQL SSL mode (default `prefer`) |
| `EMAIL_HOST` | yes (for contact form) | SMTP host; without it, emails print to the console |
| `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | with SMTP | SMTP credentials |
| `EMAIL_BACKEND` | no | Override the email backend explicitly |
| `DEFAULT_FROM_EMAIL` | recommended | From-address for outgoing mail |
| `CONTACT_EMAIL` | recommended | Where contact-form messages are delivered |
| `SECURE_SSL_REDIRECT` | no | `True` to redirect HTTP→HTTPS at Django level |
| `SECURE_HSTS_SECONDS` | no | Enable HSTS once HTTPS is confirmed |

## Publishing workflow

1. Write the article as plain text in the admin (blank line = new paragraph).
2. Add an **excerpt** (one-sentence summary) — it appears in listings and meta descriptions.
3. Keep status as **Draft** until ready; only **Published** posts are visible publicly.
4. The publication date shown to readers is `created_at`; later edits surface as "Updated".

Article URLs are SEO-friendly and date-based: `/articles/<year>/<month>/<day>/<slug>/`.
Old `/post/<id>/` links redirect permanently to the canonical URL.

## Project layout

```
blog/               # the app: models, views, templates-in-templates, tests
blog_project/       # settings, root URLs, WSGI
templates/blog/     # page templates (base, index, blog, post, about, contact)
static/             # CSS, JS, images (served by WhiteNoise in production)
```

## Roadmap

Version 1.0 (current) = a credible public resource: working reading journey,
editorial principles, sitemap/structured data, contact form, newsletter capture.
Deferred to later phases per the project brief: topic categories/tags, search,
comments, reading paths, analytics and content experimentation tooling.