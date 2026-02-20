// === Canvas Renderer ===

import { BUILDING_DEFINITIONS, CANVAS, GRID_SIZE, TOWER_DEFINITIONS } from "../core/config.js";
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
  ctx.lineWidth = 28;
  ctx.strokeStyle = "rgba(110, 143, 196, 0.28)";
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  ctx.beginPath();
  ctx.moveTo(path.waypoints[0].x, path.waypoints[0].y);

  for (let i = 1; i < path.waypoints.length; i += 1) {
    ctx.lineTo(path.waypoints[i].x, path.waypoints[i].y);
  }
  ctx.stroke();

  ctx.lineWidth = 4;
  ctx.strokeStyle = "rgba(192, 220, 255, 0.52)";
  ctx.stroke();
}

function drawTowerSlots(ctx: CanvasRenderingContext2D, state: GameState): void {
  for (const slot of state.towerSlots) {
    ctx.beginPath();
    ctx.arc(slot.position.x, slot.position.y, 16, 0, Math.PI * 2);

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

    ctx.beginPath();
    ctx.arc(slot.position.x, slot.position.y, 14, 0, Math.PI * 2);
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
    const size = 23;

    ctx.fillStyle = def.color;
    ctx.fillRect(slot.position.x - size / 2, slot.position.y - size / 2, size, size);

    ctx.strokeStyle = "rgba(14, 24, 42, 0.75)";
    ctx.lineWidth = 2;
    ctx.strokeRect(slot.position.x - size / 2, slot.position.y - size / 2, size, size);
  }
}

function drawEnemies(ctx: CanvasRenderingContext2D, state: GameState, path: PathModel): void {
  for (const enemy of state.enemies) {
    const pos = samplePathPosition(path, enemy.pathProgress);

    ctx.beginPath();
    ctx.arc(pos.x, pos.y, enemy.radius, 0, Math.PI * 2);
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
    ctx.beginPath();
    ctx.arc(projectile.position.x, projectile.position.y, projectile.radius, 0, Math.PI * 2);
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
