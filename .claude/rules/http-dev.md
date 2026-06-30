---
paths:
  - "http/**"
---

# HTTP dev files (`http/`)

REST Client (humao.rest-client) `.http` files live in `http/`.

## Environment variable workflow

Shared values live in a standard `.env` file and are read by REST Client's
`{{$dotenv VAR}}` system variable.

| File | Committed? | Purpose |
|------|-----------|---------|
| `http/.env.example` | Yes | Template — safe to commit, placeholders only |
| `http/.env` | No (gitignored) | Per-machine copy with real values |

**Key behavior (do not regress):**
- `{{$dotenv VAR}}` reads the `.env` located in the **same directory as the
  `.http` file** (i.e. `http/.env`), so every `.http` under `http/` shares it.
- Plain `@file` variables are **file-scoped** — they are NOT shared across
  `.http` files. Use `{{$dotenv VAR}}` for anything that must be shared; use
  `@var` only for values constant within a single file (e.g. `@content_type`).

**When helping with HTTP files:**
- Never write real credentials or tokens into `.env.example`.
- If `http/.env` does not exist yet, remind the user to create it:
  `cp http/.env.example http/.env`
- Keep `.env.example` in sync with `.env` whenever a new variable is added —
  add a placeholder value, not a real one.

## Authoring new `.http` files

- Reference shared values via `{{$dotenv VAR_NAME}}` (defined in `http/.env`).
- Use `@var` for file-local constants (e.g. `@content_type = application/json`).
- Use `@name <label>` on a request block to enable response-variable chaining in
  subsequent requests (`{{<label>.response.body.<jsonPath>}}`).
- Built-in dynamic variables that need no setup: `{{$guid}}`, `{{$timestamp}}`,
  `{{$datetime iso8601}}`, `{{$randomInt min max}}`.
- See `http/sample.http` for a working reference of all common patterns.

## Sending data files (CSV, etc.)

When a request needs to send file contents (CSV, JSON, XML, plain text, …):

- Put the data file in **`http/data/`** (a shared, general-purpose folder — not
  CSV-only). Keep `.http` files and their payloads separate.
- Reference it from the `.http` file by a path **relative to that `.http` file**
  (so `http/` is the base): `./data/<file>`.
  - `< ./data/<file>` — send the file as-is (no variable substitution).
  - `<@ ./data/<file>` — substitute `{{variables}}` inside the file first; add an
    encoding when the file is not UTF-8 (e.g. `<@latin1 ./data/legacy.csv`).
- Set an appropriate `Content-Type` (e.g. `text/csv`), or include the file as one
  part of a `multipart/form-data` body (`Content-Disposition: ...; filename=...`
  then `< ./data/<file>`).
- Do NOT commit sensitive or large real datasets — keep only sample/reference
  files under version control; gitignore real data files individually if needed.
- See sections 13–14 of `http/sample.http` and `http/data/sample.csv`.
