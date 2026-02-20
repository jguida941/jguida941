// === Math Utilities ===

import type { Vec2 } from "./types.js";

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function distanceSquared(a: Vec2, b: Vec2): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return dx * dx + dy * dy;
}

export function distance(a: Vec2, b: Vec2): number {
  return Math.sqrt(distanceSquared(a, b));
}

export function normalize(v: Vec2): Vec2 {
  const mag = Math.hypot(v.x, v.y);
  if (mag <= 0.0001) {
    return { x: 0, y: 0 };
  }
  return { x: v.x / mag, y: v.y / mag };
}

export function subtract(a: Vec2, b: Vec2): Vec2 {
  return { x: a.x - b.x, y: a.y - b.y };
}

export function add(a: Vec2, b: Vec2): Vec2 {
  return { x: a.x + b.x, y: a.y + b.y };
}

export function multiply(v: Vec2, scalar: number): Vec2 {
  return { x: v.x * scalar, y: v.y * scalar };
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}
