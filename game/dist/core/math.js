// === Math Utilities ===
export function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}
export function distanceSquared(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return dx * dx + dy * dy;
}
export function distance(a, b) {
    return Math.sqrt(distanceSquared(a, b));
}
export function normalize(v) {
    const mag = Math.hypot(v.x, v.y);
    if (mag <= 0.0001) {
        return { x: 0, y: 0 };
    }
    return { x: v.x / mag, y: v.y / mag };
}
export function subtract(a, b) {
    return { x: a.x - b.x, y: a.y - b.y };
}
export function add(a, b) {
    return { x: a.x + b.x, y: a.y + b.y };
}
export function multiply(v, scalar) {
    return { x: v.x * scalar, y: v.y * scalar };
}
export function lerp(a, b, t) {
    return a + (b - a) * t;
}
