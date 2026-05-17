# GitHub CLI Recipes

Use `gh` for GitHub state. Always specify `--repo owner/repo` when not inside the target repository.

## PR Overview

```bash
gh pr view <number-or-url> \
  --json number,title,state,url,author,baseRefName,headRefName,mergeable,reviewDecision,isDraft
```

## Checks

```bash
gh pr checks <number-or-url> --watch=false
```

## Reviews And Comments

```bash
gh pr view <number-or-url> \
  --json reviews,comments,latestReviews,reviewDecision
```

## Review Threads Through GraphQL

```bash
gh api graphql -f query='
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes {
          isResolved
          comments(first:20) {
            nodes {
              author { login }
              body
              createdAt
            }
          }
        }
      }
    }
  }
}' -F owner=OWNER -F repo=REPO -F number=123
```

## PR Body Template

```markdown
## Summary
- ...

## Linear
- LUC-123: https://linear.app/luckee20/issue/LUC-123

## Tests
- `command`: result

## Risks
- ...
```

