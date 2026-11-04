# CI, releases and deploys

**Publishing is not deploying.**

1. A push to `main` in an app repo builds `sha-<7>`, pushes it, and bumps the chart values in
   `{{app}}-charts`. The result is a *candidate*.
2. Bumping `Chart.yaml` `version:` together with a CHANGELOG section publishes an immutable chart.
3. Moving the pin to that chart version in an environment is the deploy.

## App repo CI (`.github/workflows/ci.yml`, `name: CI`)

- **Triggers:** push to `main` **and** pull requests. Work often lands straight on main, so a
  PR-only trigger would skip checks.
- **Python job `test`:** `astral-sh/setup-uv`, then `uv sync --frozen`, `uv run ruff check`,
  `uv run pytest -v`. Private git deps are authorized with `git config url.insteadOf` and the
  `BUILD_TOKEN` secret.
- **Web job `check`:** `pnpm/action-setup` + `actions/setup-node`, then
  `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm typecheck`, `pnpm check:colors`.
- **The `deploy` job** runs only on a push to main, after the checks. It calls the charts repo's
  reusable workflow:
  ```yaml
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions: { contents: read, packages: write }
    uses: {{org}}/{{app}}-charts/.github/workflows/build-and-deploy.yml@v1
    with:
      image: ghcr.io/{{org}}/{{app}}-api
      value_keys: |
        .api.image.tag
    secrets:
      build_token: ${{ secrets.BUILD_TOKEN }}
      infra_token: ${{ secrets.INFRA_TOKEN }}
  ```
  `value_keys` lists several keys when one image serves several components (an API and its
  worker).

## Reusable `build-and-deploy.yml` (charts repo)

- **Inputs:** `image`, `value_keys`, `context` (default `.`), `platforms` (default
  `linux/amd64`), `infra_repo`, `values_file`. **Secrets:** `build_token`, `infra_token`.
- **Job settings:** `timeout-minutes: 30`. Concurrency group
  `build-${{ github.repository }}-${{ github.ref }}-${{ inputs.image }}` with
  `cancel-in-progress: true`.
- **Steps:**
  1. Compute the tag: `sha-${GITHUB_SHA::7}`.
  2. Run buildx, log in to ghcr with `GITHUB_TOKEN`, and run `build-push-action` with
     `secrets: gh_token=…`, tagging both `:sha-xxx` and `:latest`.
  3. Bump: clone the charts repo, `yq -i "<key> = strenv(TAG)"` for each key, commit
     `deploy: <image>:<tag>` as github-actions[bot], and exit 0 if there is no diff.
  4. Push with up to 5 `git pull --rebase --autostash` retries.
- **The header says the bump is not a deploy.**
- **Pin callers to a moving major tag (`@v1`), never `@main`.** After editing the workflow, move
  the tag: `git tag -fa v1 && git push -f origin v1`.

## Charts repo CI

- **`ci.yml`** (PR + push):
  - **`helm` job:** `helm dependency build`, `helm lint`, then `helm template` for each
    supported install shape. It asserts that a render with a missing required value **fails**,
    and that the vendored `.tgz` files match `Chart.lock`.
  - **`shell` job:** `git ls-files '*.sh' | xargs -r -n1 bash -n`, plus shellcheck.
  - **`compose` job:** `docker compose -f local/docker-compose.yml config -q`.
- **`chart-publish.yml`** (push to main, paths `charts/**`). For each chart:
  1. If `helm show chart oci://… --version $VERSION` already succeeds, emit a `::notice::` and
     skip.
  2. Extract the `## [$VERSION]` CHANGELOG section, and fail if it is empty.
  3. `helm package` + `helm push oci://ghcr.io/{{org}}/charts`.
  4. `git tag -a <chart>-<version>`, then `gh release create` with the notes.

## Tags and names

| Thing | Form |
|---|---|
| Image | `ghcr.io/{{org}}/<repo>` |
| Image tag | `sha-<7>` (immutable); `latest` is pushed but never referenced |
| Chart | `oci://ghcr.io/{{org}}/charts/<chart>` |
| Chart git tag | `<chart>-<version>` |
| Reusable workflow tags | `v1` (moving) + `v1.x.y` |

## Environments and GitOps (when there is more than one)

- Per-environment configuration lives in a `<client>-env` repo. It holds a values file per
  release plus `version:`, the chart version it pins.
- An Argo CD Application (or ApplicationSet, one Application per file) tracks it.
- A deploy is a PR that moves the pin. A rollback is a PR that moves it back.
- Renovate opens those PRs. It is run **manually** (`workflow_dispatch`), because cutting a
  release and looking for one are both decisions:
  - It uses regex managers on `^version:`.
  - There is no automerge, and first-party images are excluded.

## Renovate (app repos)

`renovate.json` exists only to opt in. It enables just the managers you want: e.g. only `npm`,
for the org's own scope (`"matchPackageNames": ["@<scope>/**"]`), so third-party noise doesn't
bury internal pins. Every rule has a `description`.
