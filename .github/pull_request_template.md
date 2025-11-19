# Pull Request Template

## What was fixed
- **ISSUE**: [AUDIT][ID] - Title
- Brief description of changes
- Files/functions modified

## How to test locally
1. Commands to reproduce the issue
2. Environment setup: set environment variables
3. Run: `pytest -q tests/test_<id>.py`

## Acceptance criteria
- [ ] Static scan passes (bandit, safety)
- [ ] Unit tests pass
- [ ] Golden retrieval: hit@5 >= 0.95 (local test)
- [ ] No secret strings in repo

## Security checklist
- [ ] No hardcoded secrets added
- [ ] Input validation implemented
- [ ] Error handling doesn't leak sensitive info
- [ ] Authentication/authorization properly implemented

## Performance impact
- [ ] No significant performance degradation
- [ ] Database queries optimized
- [ ] Caching strategy considered

## Rollout plan
- [ ] Merge to staging
- [ ] Run smoke tests
- [ ] Canary 5% traffic
- [ ] Promote to prod

## Related issues
- Closes #[issue_number]
- Related to #[issue_number]

---

## Review checklist (for reviewers)
- [ ] Code follows project standards
- [ ] Tests cover the changes
- [ ] Documentation updated if needed
- [ ] Security implications considered
- [ ] Performance impact assessed