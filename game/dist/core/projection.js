// === Screen Projection Helpers ===
import { CANVAS } from "./config.js";
const TILT_Y = 0.78;
const SKEW_X = 0.18;
const OFFSET_Y = 44;
export function worldToScreen(world) {
    const fromCenterY = world.y - CANVAS.height * 0.5;
    return {
        x: world.x + fromCenterY * SKEW_X,
        y: world.y * TILT_Y + OFFSET_Y,
    };
}
export function screenToWorld(screen) {
    const worldY = (screen.y - OFFSET_Y) / TILT_Y;
    const fromCenterY = worldY - CANVAS.height * 0.5;
    return {
        x: screen.x - fromCenterY * SKEW_X,
        y: worldY,
    };
}
