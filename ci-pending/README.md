# Pending CI workflow

`ci.yml` here is the GitHub Actions workflow that should live at
`.github/workflows/ci.yml`. It was pushed under this path because the current
`gh` OAuth token lacks `workflow` scope and GitHub refuses to accept commits
that touch `.github/workflows/` without it.

To activate it:

```bash
gh auth refresh -h github.com -s workflow
mkdir -p .github/workflows
git mv ci-pending/ci.yml .github/workflows/ci.yml
git rm ci-pending/README.md
rmdir ci-pending
git commit -m "ci: enable GitHub Actions workflow"
git push
```
