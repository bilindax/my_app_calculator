"""Room metrics (compatibility layer)

This module provides the legacy `build_room_metrics_context` and
`calculate_room_finish_metrics` APIs expected by some UI flows and tests.

Implementation is a thin adapter over `UnifiedCalculator` so that all
finish calculations come from a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

from bilind.calculations.unified_calculator import UnifiedCalculator


@dataclass(frozen=True)
class RoomMetricsContext:
    """Reusable calculation context.

    The original design used prebuilt lookup maps; we now route through
    `UnifiedCalculator` but keep this context object so callers don't need
    to change.
    """

    rooms: List[Any]
    doors: List[Any]
    windows: List[Any]
    ceramic_zones: List[Any]
    default_wall_height: float = 3.0


@dataclass(frozen=True)
class RoomFinishMetrics:
    """Finish metrics for a single room (legacy shape)."""

    room_name: str
    area: float

    wall_finish_net: float

    plaster_total: float
    paint_total: float

    ceramic_wall: float
    ceramic_ceiling: float
    ceramic_floor: float
    ceramic_total: float


class _ProjectView:
    """Minimal project-like object for UnifiedCalculator."""

    def __init__(
        self,
        rooms: Iterable[Any],
        doors: Iterable[Any],
        windows: Iterable[Any],
        ceramic_zones: Iterable[Any],
    ) -> None:
        self.rooms = list(rooms or [])
        self.doors = list(doors or [])
        self.windows = list(windows or [])
        self.ceramic_zones = list(ceramic_zones or [])


class RoomMetrics:
    """Legacy metrics helper.

    Some older flows (and tests) expect a per-room object with a
    `compute_metrics()` method returning a dict.

    All core quantities come from `UnifiedCalculator`.
    A minimal fallback keeps older wall-level ceramic fields working when no
    ceramic zones are present.
    """

    def __init__(self, room: Any, project: Any):
        self.room = room
        self.project = project

    def compute_metrics(self) -> dict:
        calc = UnifiedCalculator(self.project)
        rc = calc.calculate_room(self.room)

        cer_wall = float(rc.ceramic_wall or 0.0)
        cer_floor = float(rc.ceramic_floor or 0.0)
        cer_ceil = float(rc.ceramic_ceiling or 0.0)

        # Legacy fallback: if there are no ceramic zones at all, allow per-wall
        # `ceramic_area` values to contribute to wall ceramic.
        try:
            zones = getattr(self.project, 'ceramic_zones', None)
            has_any_zones = bool(zones)
        except Exception:
            has_any_zones = False

        if not has_any_zones:
            try:
                walls = self.room.get('walls', []) if isinstance(self.room, dict) else (getattr(self.room, 'walls', []) or [])
                extra = 0.0
                for w in (walls or []):
                    if isinstance(w, dict):
                        extra += float(w.get('ceramic_area', 0.0) or 0.0)
                    else:
                        extra += float(getattr(w, 'ceramic_area', 0.0) or 0.0)
                cer_wall += extra
            except Exception:
                pass

        plaster_walls = float(rc.plaster_walls or 0.0)
        plaster_ceil = float(rc.plaster_ceiling or 0.0)
        plaster_total = plaster_walls + plaster_ceil

        paint_walls = max(0.0, plaster_walls - cer_wall)
        paint_ceil = max(0.0, plaster_ceil - cer_ceil)
        paint_total = paint_walls + paint_ceil

        return {
            'room_name': str(rc.room_name or ''),
            'walls_gross': float(rc.walls_gross or 0.0),
            'openings_total': float(rc.walls_openings or 0.0),
            'walls_net': float(rc.walls_net or 0.0),
            'area': float(rc.ceiling_area or 0.0),
            'plaster_total': plaster_total,
            'paint_total': paint_total,
            'cer_wall': cer_wall,
            'cer_floor': cer_floor,
            'cer_ceil': cer_ceil,
        }


def build_room_metrics_context(
    rooms: List[Any],
    doors: List[Any],
    windows: List[Any],
    ceramic_zones: Optional[List[Any]] = None,
    default_wall_height: float = 3.0,
) -> RoomMetricsContext:
    return RoomMetricsContext(
        rooms=list(rooms or []),
        doors=list(doors or []),
        windows=list(windows or []),
        ceramic_zones=list(ceramic_zones or []),
        default_wall_height=float(default_wall_height or 3.0),
    )


def calculate_room_finish_metrics(room: Any, ctx: RoomMetricsContext) -> RoomFinishMetrics:
    """Calculate finishes for one room using the SSOT UnifiedCalculator."""

    project_view = _ProjectView(
        rooms=ctx.rooms,
        doors=ctx.doors,
        windows=ctx.windows,
        ceramic_zones=ctx.ceramic_zones,
    )

    # Ensure the room has a wall height if it was omitted.
    # (Some legacy dict rooms used `default_wall_height` only.)
    try:
        if isinstance(room, dict):
            room.setdefault('wall_height', ctx.default_wall_height)
        else:
            if getattr(room, 'wall_height', None) in (None, 0, 0.0):
                setattr(room, 'wall_height', ctx.default_wall_height)
    except Exception:
        pass

    calc = UnifiedCalculator(project_view)
    rc = calc.calculate_room(room)

    ceramic_total = float(rc.ceramic_wall or 0.0) + float(rc.ceramic_ceiling or 0.0) + float(rc.ceramic_floor or 0.0)

    # NOTE: `wall_finish_net` in the UI means the net wall area after openings.
    return RoomFinishMetrics(
        room_name=str(rc.room_name or ''),
        area=float(rc.ceiling_area or 0.0),
        wall_finish_net=float(rc.walls_net or 0.0),
        plaster_total=float(rc.plaster_total or 0.0),
        paint_total=float(rc.paint_total or 0.0),
        ceramic_wall=float(rc.ceramic_wall or 0.0),
        ceramic_ceiling=float(rc.ceramic_ceiling or 0.0),
        ceramic_floor=float(rc.ceramic_floor or 0.0),
        ceramic_total=ceramic_total,
    )
