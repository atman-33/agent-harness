---
paths:
  - ../*/.github/workflows/**
---

# GitHub Actions ワークフロー構文の落とし穴

## `secrets` コンテキストは `if:` 条件式では使えない

`jobs.<job_id>.if` でも `jobs.<job_id>.steps.if` でも、`secrets.FOO != ''` のように
`secrets` コンテキストを直接 `if:` に書くと、YAML構文自体は正しくても GitHub Actions の
ワークフロー検証で "Invalid workflow file" / "Unrecognized named-value: 'secrets'" として
弾かれ、そのワークフローファイル全体（他のジョブも含む）が動かなくなる。

回避策: 一度 `env:` に格納し、`if:` では `env` コンテキスト経由で判定する。

```yaml
jobs:
  my-job:
    env:
      MY_SECRET: ${{ secrets.MY_SECRET }}
    steps:
      - if: ${{ env.MY_SECRET != '' }}
        run: ...
```

Secretsが未設定なら特定ジョブ/ステップをスキップする、という「条件付き実行」を
書く際は必ずこのパターンを使うこと。

## CIでの外部CLI出力のパースは決め打ちしない

CIから叩く外部CLI（Supabase CLI等）の標準出力形式は、ローカル実行環境とGitHub Actions
ランナーとで異なることがある（例: 同じコマンドでもJSON出力とテーブル形式出力が環境に
よって切り替わるケースを実際に確認した）。CIスクリプトで外部コマンドの出力をパースする
場合は、単一の出力形式を前提にせず、複数の形式を試すフォールバックを入れるか、
機械可読性が保証された明示的なフラグ・専用APIを優先する。
