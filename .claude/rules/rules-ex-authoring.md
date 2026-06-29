---
paths:
  - ".claude/rules-ex/**"
---

# Authoring `.claude/rules-ex/*.md` (extended rules)

You are editing a file under `.claude/rules-ex/`. These are **extended rules** — a
custom mechanism, **not** a native Claude Code feature. They only take effect via
the `engineering@atman-marketplace` plugin's `inject-extended-rules` hook (Claude
Code) and the OpenCode mirror `.opencode/plugins/inject-extended-rules-plugin.ts`.
Contrast with `.claude/rules` (native, governs this repo's own files).

Follow this format when creating or editing a rule here:

- **`paths:` is REQUIRED.** A rule with no `paths:` front matter is skipped (a
  cross-cutting rule must declare its scope, or it would fire on every file). The
  folder's `README.md` has no `paths:` precisely so it is ignored.
- **Globs are workspace-relative (cwd = agent-harness).** Use `..` to reach sibling
  repos, e.g. `../atman-marketplace/plugins/**/*.mjs`. A bare `src/**` would target
  agent-harness itself.
- **Matching is strict and root-anchored** — full match from the workspace root, no
  implicit leading `**/` prefix. Use `**` for any depth: `../repo/**/*.ts`. `*`
  matches a single path segment; `?` a single character.
- **Body = the injected rule.** Everything below the front matter is what gets
  injected into context (wrapped in `<extended-rules>`), once per rule per agent
  context per session. Keep it focused and imperative.

```markdown
---
paths:
  - ../atman-marketplace/plugins/**/*.mjs
---
In atman-marketplace .mjs hook scripts: zero dependencies, Node built-ins only.
```

For the full design (de-dup, both injection paths, OpenCode mirror) see
`.claude/rules/harness-internals.md`.
