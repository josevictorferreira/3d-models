"""Every part under projects/ must build into a valid solid."""

import pytest
from build123d import Part

from cadlib.cli import PROJECTS, find_parts, load_part


@pytest.mark.parametrize("source", find_parts(), ids=lambda p: str(p.relative_to(PROJECTS)))
def test_part_builds(source):
    part = load_part(source)
    assert isinstance(part, Part)
    assert part.is_valid
    assert part.volume > 0
