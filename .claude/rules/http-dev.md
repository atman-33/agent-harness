---
paths:
  - "http/**"
---

# HTTP dev files (`http/`)

REST Client (humao.rest-client) `.http` files live in `http/`.

## Environment variable workflow

| File | Committed? | Purpose |
|------|-----------|---------|
| `http/_env.example.http` | Yes | Template — safe to commit, no real secrets |
| `http/_env.http` | No (gitignored) | Per-machine copy with real values |

**When helping with HTTP files:**
- Never write real credentials or tokens into `_env.example.http`.
- If `_env.http` does not exist yet, remind the user to create it:
  `cp http/_env.example.http http/_env.http`
- Keep `_env.example.http` in sync with `_env.http` whenever a new variable is
  added — update the example with a placeholder value, not a real one.

## Authoring new `.http` files

- Reference shared variables via `{{variable_name}}` (defined in `_env.http`).
- Use `@name <label>` on a request block to enable response-variable chaining in
  subsequent requests (`{{<label>.response.body.<jsonPath>}}`).
- Built-in dynamic variables that need no setup: `{{$guid}}`, `{{$timestamp}}`,
  `{{$datetime iso8601}}`, `{{$randomInt min max}}`.
- See `http/sample.http` for a working reference of all common patterns.
