## Summary

<!-- Describe the change and its motivation. -->

## Release impact

Select exactly one option. Update `project.version` in `pyproject.toml` to match:

- For PRs into `main`, use a stable `X.Y.Z` version.
- For PRs into `dev`, use a beta `X.Y.ZbN` version.

- [ ] `patch` — backward-compatible bug fix or small correction
- [ ] `minor` — backward-compatible functionality
- [ ] `major` — backward-incompatible change

The CI checks that the selected impact and version match the target branch.

## Validation

- [ ] Tests pass locally or the reason they could not be run is described.
- [ ] Documentation is updated when needed.
