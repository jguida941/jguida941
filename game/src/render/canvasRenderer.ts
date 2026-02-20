// === Canvas Renderer ===

import { BUILDING_DEFINITIONS, CANVAS, GRID_SIZE, TOWER_DEFINITIONS } from "../core/config.js";
import { worldToScreen } from "../core/projection.js";
import { samplePathPosition } from "../systems/pathing.js";
import type { GameState, PathModel } from "../core/types.js";

function drawGrid(ctx: CanvasRenderingContext2D): void {
  ctx.strokeStyle = "rgba(165, 196, 255, 0.08)";
  ctx.lineWidth = 1;

  for (let x = 0; x <= CANVAS.width; x += GRID_SIZE) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, CANVAS.height);
    ctx.stroke();
  }

  for (let y = 0; y <= CANVAS.height; y += GRID_SIZE) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(CANVAS.width, y);
    ctx.stroke();
  }
}

function drawPath(ctx: CanvasRenderingContext2D, path: PathModel): void {
  ctx.lineWidth = 24;
  ctx.strokeStyle = "rgba(110, 143, 196, 0.28)";
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  const start = worldToScreen(path.waypoints[0]);
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);

  for (let i = 1; i < path.waypoints.length; i += 1) {
    const point = worldToScreen(path.waypoints[i]);
    ctx.lineTo(point.x, point.y);
  }
  ctx.stroke();

  ctx.lineWidth = 3;
  ctx.strokeStyle = "rgba(192, 220, 255, 0.52)";
  ctx.stroke();
}

function drawTowerSlots(ctx: CanvasRenderingContext2D, state: GameState): void {
  for (const slot of state.towerSlots) {
    const point = worldToScreen(slot.position);
    ctx.beginPath();
    ctx.ellipse(point.x, point.y, 18, 13, 0, 0, Math.PI * 2);

    if (slot.towerId !== null) {
      ctx.fillStyle = "rgba(121, 239, 173, 0.28)";
    } else if (slot.buildingId !== null) {
      ctx.fillStyle = "rgba(255, 222, 135, 0.28)";
    } else {
      ctx.fillStyle = "rgba(157, 186, 234, 0.26)";
    }

    ctx.fill();
    ctx.strokeStyle = "rgba(191, 223, 255, 0.62)";
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawTowers(ctx: CanvasRenderingContext2D, state: GameState): void {
  for (const tower of state.towers) {
    const slot = state.towerSlots.find((candidate) => candidate.id === tower.slotId);
    if (!slot) {
      continue;
    }

    const def = TOWER_DEFINITIONS[tower.kind];
    const point = worldToScreen(slot.position);

    ctx.beginPath();
    ctx.ellipse(point.x, point.y + 1, 13, 10, 0, 0, Math.PI * 2);
    ctx.fillStyle = def.color;
    ctx.fill();

    ctx.strokeStyle = "rgba(14, 24, 42, 0.7)";
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawBuildings(ctx: CanvasRenderingContext2D, state: GameState): void {
  for (const building of state.buildings) {
    const slot = state.towerSlots.find((candidate) => candidate.id === building.slotId);
    if (!slot) {
      continue;
    }

    const def = BUILDING_DEFINITIONS[building.kind];
    const point = worldToScreen(slot.position);
    const width = 24;
    const height = 16;

    ctx.fillStyle = def.color;
    ctx.fillRect(point.x - width / 2, point.y - height / 2 - 5, width, height);

    ctx.fillStyle = "rgba(16, 24, 41, 0.28)";
    ctx.fillRect(point.x - width / 2 + 3, point.y - height / 2 + 10, width - 4, 9);

    ctx.strokeStyle = "rgba(14, 24, 42, 0.75)";
    ctx.lineWidth = 2;
    ctx.strokeRect(point.x - width / 2, point.y - height / 2 - 5, width, height);
  }
}

function drawEnemies(ctx: CanvasRenderingContext2D, state: GameState, path: PathModel): void {
  for (const enemy of state.enemies) {
    const worldPos = samplePathPosition(path, enemy.pathProgress);
    const pos = worldToScreen(worldPos);
    const rx = enemy.radius;
    const ry = enemy.radius * 0.84;

    ctx.beginPath();
    ctx.ellipse(pos.x, pos.y, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = enemy.color;
    ctx.fill();

    const hpRatio = Math.max(0, enemy.hp / enemy.maxHp);
    const barWidth = enemy.radius * 2;

    ctx.fillStyle = "rgba(24, 31, 49, 0.9)";
    ctx.fillRect(pos.x - barWidth / 2, pos.y - enemy.radius - 10, barWidth, 4);
    ctx.fillStyle = "#93f3a4";
    ctx.fillRect(pos.x - barWidth / 2, pos.y - enemy.radius - 10, barWidth * hpRatio, 4);
  }
}

function drawProjectiles(ctx: CanvasRenderingContext2D, state: GameState): void {
  for (const projectile of state.projectiles) {
    const pos = worldToScreen(projectile.position);
    ctx.beginPath();
    ctx.ellipse(pos.x, pos.y, projectile.radius, projectile.radius * 0.85, 0, 0, Math.PI * 2);
    ctx.fillStyle = "#e8f5ff";
    ctx.fill();
  }
}

function drawCanvasOverlay(ctx: CanvasRenderingContext2D, state: GameState): void {
  ctx.fillStyle = "rgba(7, 14, 29, 0.74)";
  ctx.fillRect(10, 10, 300, 96);

  ctx.fillStyle = "#d8e7ff";
  ctx.font = "13px 'Press Start 2P', monospace";
  ctx.fillText(`Stage ${state.stage}-${state.wave}`, 20, 35);

  ctx.font = "14px 'Space Grotesk', sans-serif";
  ctx.fillText(`Phase: ${state.phase.toUpperCase()}`, 20, 57);
  ctx.fillText(`Enemies: ${state.enemies.length}`, 20, 76);
  ctx.fillText(`Mode: ${state.placementMode.toUpperCase()}`, 20, 95);
}

export function renderCanvas(
  ctx: CanvasRenderingContext2D,
  state: GameState,
  path: PathModel,
): void {
  const gradient = ctx.createLinearGradient(0, 0, 0, CANVAS.height);
  gradient.addColorStop(0, "#0f1a34");
  gradient.addColorStop(1, "#162446");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, CANVAS.width, CANVAS.height);

  drawGrid(ctx);
  drawPath(ctx, path);
  drawTowerSlots(ctx, state);
  drawBuildings(ctx, state);
  drawTowers(ctx, state);
  drawEnemies(ctx, state, path);
  drawProjectiles(ctx, state);
  drawCanvasOverlay(ctx, state);
}
