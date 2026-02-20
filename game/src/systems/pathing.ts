// === Pathing System ===

import { PATH_WAYPOINTS } from "../core/config.js";
import { clamp, lerp, normalize, subtract } from "../core/math.js";
import type { PathModel, PathSegment, Vec2 } from "../core/types.js";

function createSegments(waypoints: Vec2[]): PathSegment[] {
  const segments: PathSegment[] = [];
  let cumulativeLength = 0;

  for (let i = 0; i < waypoints.length - 1; i += 1) {
    const start = waypoints[i];
    const end = waypoints[i + 1];
    const length = Math.hypot(end.x - start.x, end.y - start.y);
    cumulativeLength += length;

    segments.push({
      start,
      end,
      length,
      cumulativeLength,
    });
  }

  return segments;
}

export function createPathModel(): PathModel {
  const waypoints = [...PATH_WAYPOINTS];
  const segments = createSegments(waypoints);
  const length = segments.length ? segments[segments.length - 1].cumulativeLength : 1;

  return {
    waypoints,
    segments,
    length,
  };
}

export function samplePathPosition(path: PathModel, progress: number): Vec2 {
  const normalizedProgress = clamp(progress, 0, 1);
  const targetDistance = normalizedProgress * path.length;

  let previousDistance = 0;
  for (const segment of path.segments) {
    if (targetDistance <= segment.cumulativeLength) {
      const segmentDistance = targetDistance - previousDistance;
      const t = segment.length <= 0.0001 ? 0 : segmentDistance / segment.length;
      return {
        x: lerp(segment.start.x, segment.end.x, t),
        y: lerp(segment.start.y, segment.end.y, t),
      };
    }
    previousDistance = segment.cumulativeLength;
  }

  const finalWaypoint = path.waypoints[path.waypoints.length - 1] ?? { x: 0, y: 0 };
  return finalWaypoint;
}

export function samplePathDirection(path: PathModel, progress: number): Vec2 {
  const normalizedProgress = clamp(progress, 0, 1);
  const targetDistance = normalizedProgress * path.length;

  let previousDistance = 0;
  for (const segment of path.segments) {
    if (targetDistance <= segment.cumulativeLength) {
      return normalize(subtract(segment.end, segment.start));
    }
    previousDistance = segment.cumulativeLength;
  }

  const finalSegment = path.segments[path.segments.length - 1];
  if (!finalSegment) {
    return { x: 1, y: 0 };
  }
  return normalize(subtract(finalSegment.end, finalSegment.start));
}
