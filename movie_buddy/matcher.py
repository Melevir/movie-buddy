from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from movie_buddy.models import Content


def rank_results(
    results: list[Content],
    *,
    watching_ids: set[int],
    bookmark_ids: set[int],
) -> tuple[Content | None, str | None]:
    if len(results) == 1:
        return results[0], None

    watching_matches = [r for r in results if r.id in watching_ids]
    if len(watching_matches) == 1:
        return watching_matches[
            0
        ], f"In your watching list: {watching_matches[0].title}"

    bookmark_matches = [r for r in results if r.id in bookmark_ids]
    if len(bookmark_matches) == 1:
        return bookmark_matches[0], f"In your bookmarks: {bookmark_matches[0].title}"

    return None, None
