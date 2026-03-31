# Listmonk Newsletter Digest

Automatically generate and schedule [listmonk](https://listmonk.app) newsletter campaigns from RSS feeds or Discourse forums. Runs on a cron schedule, tracks which posts have already been sent, and only emails new content.

This is a fork of [iloveitaly/listmonk-newsletter](https://github.com/iloveitaly/listmonk-newsletter) with significant enhancements.

## Enhancements Over Upstream

- **Discourse support** — pull entries from a Discourse JSON API endpoint in addition to RSS
- **Multi-environment support** — run separate newsletter instances from one deployment, each with isolated state and templates via `DATA_SUBDIRECTORY`
- **OG metadata** — automatically fetches `og:image` and `og:description` for each post and makes them available in templates
- **Dynamic titles** — `LISTMONK_TITLE` supports `strftime` format codes (e.g. `"Weekly Digest %-m/%-d/%y"`)
- **Dynamic subheader** — title is passed into the Jinja2 template context for use as a subheader
- **Configurable feed limit** — `FEED_MAX_ITEMS` caps how many posts appear per campaign
- **API token auth** — uses `LISTMONK_API_TOKEN` instead of a password

## How It Works

On each run, the tool:

1. Fetches entries from your RSS feed or Discourse forum
2. Compares them against a list of previously sent links (`processed_links.txt`)
3. Fetches `og:image` and `og:description` for each new entry
4. Optionally fetches Readwise articles and/or a GitHub activity summary
5. Renders a Jinja2 email template with all of this content
6. Creates a listmonk campaign and either sends it immediately or schedules it
7. Updates the processed links file so entries aren't sent twice

On the very first run, the most recent `FEED_MAX_ITEMS` entries are sent. After that, only new entries trigger a campaign. If there are no new entries, nothing is sent.

## Prerequisites

- A running [listmonk](https://listmonk.app) instance
- A listmonk list to send to
- A listmonk template ID — use an empty passthrough template that just renders `{{{ message }}}`
- A listmonk API token (Settings → Users → API tokens)

## Configuration

All configuration is via environment variables. See [.envrc-example](.envrc-example) for a complete reference.

### Required

| Variable | Description |
|---|---|
| `LISTMONK_URL` | Base URL of your listmonk instance |
| `LISTMONK_USERNAME` | listmonk username |
| `LISTMONK_API_TOKEN` | listmonk API token |
| `LISTMONK_TEMPLATE` | listmonk template ID (use a blank passthrough template) |
| `LISTMONK_LISTS` | Comma-separated list IDs to send to |
| `LISTMONK_TITLE` | Campaign title/subject. Supports `strftime` codes, e.g. `"Blog Digest %-m/%-d/%y"` |
| `RSS_URL` or `DISCOURSE_JSON_URL` | Feed source (use one) |

### Optional

| Variable | Default | Description |
|---|---|---|
| `FEED_MAX_ITEMS` | `5` | Max feed entries per campaign |
| `DATA_SUBDIRECTORY` | _(none)_ | Subdirectory under `data/` for this environment's state and template |
| `SCHEDULE` | `0 6 * * 1` | Cron expression for when to run |
| `LISTMONK_SEND_AT` | _(none)_ | Natural language future time to schedule sending, e.g. `"monday 5am"` |
| `LISTMONK_TEST_EMAILS` | _(none)_ | Comma-separated emails to send a test campaign to instead of launching |
| `LISTMONK_GEMINI_SUBJECT` | `false` | Use Gemini AI to generate the campaign subject line |

### Readwise Reader

| Variable | Default | Description |
|---|---|---|
| `READWISE_API_TOKEN` | _(none)_ | Readwise API token |
| `READWISE_TAG` | _(none)_ | Tag to filter articles (e.g. `"newsletter"`) |
| `READWISE_SUMMARY_DAYS` | `30` | Days to look back on first run |

### GitHub Activity Summary

| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | _(none)_ | GitHub personal access token |
| `GITHUB_USERNAME` | _(none)_ | GitHub username to summarize activity for |
| `GOOGLE_API_KEY` | _(none)_ | Google API key for Gemini |
| `GITHUB_SUMMARY_DAYS` | `30` | Days to look back |
| `GEMINI_MODEL` | `gemini-flash-latest` | Gemini model to use |

## Email Templates

Each environment's template lives at `data/<DATA_SUBDIRECTORY>/template.j2` (or `data/template.j2` if no subdirectory is set). This is a Jinja2 template that receives the following context:

| Variable | Type | Description |
|---|---|---|
| `entries` | `list[Entry]` | New feed entries to include |
| `title` | `str` | Rendered campaign title (after strftime substitution) |
| `github_summary` | `str \| None` | HTML GitHub activity summary |
| `readwise_articles` | `list[ReadwiseArticle]` | Articles from Readwise Reader |

Each `Entry` has: `title`, `link`, `description`, `summary`, `published`, `image` (og:image), `og_description`.

### Listmonk Template Variables

You can embed listmonk template variables directly in your Jinja2 template. Since listmonk uses `{{ }}` syntax too, escape them:

```html
<a href="{% raw %}{{ UnsubscribeURL }}{% endraw %}">Unsubscribe</a>
```

For link tracking, append `@TrackLink` to URLs you want tracked.

### CSS Inlining

CSS is automatically inlined before the campaign is created, so you can write normal `<style>` blocks in your template.

## Multi-Environment Setup

Run separate newsletter instances (e.g. one per blog) from a single deployment by giving each environment its own `DATA_SUBDIRECTORY`. Each subdirectory holds:

- `template.j2` — the email template for this environment
- `processed_links.txt` — tracks which posts have been sent
- `last_github_checked.txt` — GitHub activity checkpoint
- `last_readwise_checked.txt` — Readwise checkpoint

### Local Development

Use `uv run --env-file` to target a specific environment:

```sh
# run against the blog-home environment
uv run --env-file .envs/blog-home.env listmonk-newsletter

# run against the blog-business environment
uv run --env-file .envs/blog-business.env listmonk-newsletter
```

Each `.env` file sets `DATA_SUBDIRECTORY` to point at its own subdirectory:

```sh
# .envs/blog-home.env
DATA_SUBDIRECTORY=blog-home
RSS_URL=https://example.com/feed
LISTMONK_TITLE="Home Blog %-m/%-d/%y"
...
```

### Production (Docker Compose)

Define one service per environment in `docker-compose.yml`. Each service has its own env file and named volume:

```yaml
services:
  blog-home:
    image: ghcr.io/37rb/listmonk-newsletter:latest
    restart: always
    env_file:
      - .envs/blog-home.env
    environment:
      - TZ=${TZ}
    volumes:
      - blog-home-data:/app/data

  blog-business:
    image: ghcr.io/37rb/listmonk-newsletter:latest
    restart: always
    env_file:
      - .envs/blog-business.env
    environment:
      - TZ=${TZ}
    volumes:
      - blog-business-data:/app/data

volumes:
  blog-home-data:
  blog-business-data:
```

Each service has its own Docker volume, so state files are fully isolated. `DATA_SUBDIRECTORY` is still set in each env file and determines the subdirectory within `/app/data` where state and templates are stored.

> **Timezone:** The container does not inherit the host timezone automatically. Set `TZ` on the host and pass it through, or hardcode it (e.g. `TZ=America/New_York`).

## Running Locally

```sh
# install dependencies
uv sync

# run once against an environment
uv run --env-file .envs/blog-home.env listmonk-newsletter

# or with direnv + .envrc
direnv allow
uv run listmonk-newsletter
```

Useful environment overrides:

```sh
LOG_LEVEL=DEBUG uv run --env-file .envs/blog-home.env listmonk-newsletter
```

## Data Directory Layout

```
data/
  template.j2                  # default template (no DATA_SUBDIRECTORY)
  processed_links.txt          # default state

  blog-home/
    template.j2
    processed_links.txt
    last_github_checked.txt
    last_readwise_checked.txt

  blog-business/
    template.j2
    processed_links.txt
```

The `data/` directory is gitignored — copy state files off a running container with:

```sh
docker compose cp blog-home:/app/data/. data/blog-home/
```
