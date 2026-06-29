# `.claude/rules-ex` — workspace extended rules

Cross-cutting rules kept in the workspace (agent-harness) and injected when you
edit files in **other** repos, via cwd-relative globs. This is the *extended* form
of `.claude/rules` (which only governs this repo's own files).

Two complementary injection paths (engineering plugin / OpenCode mirror):

- `.claude/rules` — rules that live WITH the repo they govern (loaded by
  `inject-target-rules`).
- `.claude/rules-ex` — rules kept here, applied to ANY repo via `..` globs
  (loaded by `inject-extended-rules`).

## Rule file format

Each `*.md` here needs `paths:` front matter (REQUIRED — a rule with no `paths:`
is skipped). Globs are resolved relative to the workspace root, so use `..` to
reach sibling repos. Matching is strict and root-anchored.

```markdown
---
paths:
  - ../atman-marketplace/plugins/**/*.mjs
---
Rule text injected into context when a matching file is touched.
```

`README.md` itself has no `paths:`, so it is ignored by the hook.
