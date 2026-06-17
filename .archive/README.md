# .archive/

This directory holds files that were once part of the active repository but
have been intentionally retired. They are kept here (instead of being deleted)
so that git history and archaeology remain possible, and so that any external
tooling that still references them does not fail.

Do not put new active code, docs, or data in this directory. If you need to
reference archived content, prefer linking from current docs to this folder
rather than importing from `.archive/`.

## Contents

| File | Original location | Reason for archiving |
| --- | --- | --- |
| `Code.i18n-prelude.md` | `Code.md` (repo root) | 3.7 MB file containing a Vietnamese–Chinese–English i18n runtime prelude unrelated to the Road Finder project. Likely committed by mistake in the original repo bootstrap. |
| `repomix-output.tsp-osrm-snapshot.xml` | `repomix-output.xml` (repo root) | 75 KB repomix snapshot of the pre-pivot code state (TSP service, OSRM runtime, `/optimize-route` with `ordered_points`, `useRoutePoints` + `RouteControls`). Reflects the project before the 2026-06-04 MVP cutover. Superseded by current source. |
| _(formerly `backend/Walkthrough.md` and `frontend/Walkthrough.md`)_ | `backend/`, `frontend/` | Deleted (not moved here) because they were redundant with root `Walkthrough.md` and referenced the obsolete TSP/OSRM phase. |

## When to remove files from `.archive/`

A file should be removed from `.archive/` (and the surrounding commit history
rewritten with `git filter-repo` if you want to truly drop the bytes) only
when one of these is true:

1. The file no longer matches any artifact in the current source tree, so
   no archaeology would point back to it.
2. The file contains sensitive data (keys, customer data) and the project
   needs to physically scrub the bytes from history.
3. The file is large (multi-megabyte binary) and the storage cost outweighs
   the value of keeping it.

For normal development churn, leave `.archive/` files in place.

## Related decisions

- `docs/decisions/0008-vrp-pivot.md` — describes the broader project pivot
  that made `Code.md` and `repomix-output.xml` no longer relevant.
