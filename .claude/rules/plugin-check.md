---
paths:
  - ".opencode/plugins/**"
  - ".opencode/mcp/**"
  - ".opencode/scripts/**"
---
# Plugin / Script Check Rules

After editing any `.ts` file under `.opencode/plugins/` or any `.mjs` file
under `.opencode/mcp/` / `.opencode/scripts/`, run:

    npm run check

and confirm it exits with no errors before considering the edit complete.

- `check:ts` — type-checks `.opencode/plugins/**/*.ts` via `tsc --noEmit`
- `check:mjs` — syntax-checks `.opencode/mcp/` and `.opencode/scripts/` via `node --check`
