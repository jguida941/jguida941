// === Wave System (Build Wave / Spawn / Round Resolution) ===

import { lockClassSelection } from "./classes.js";
import type { EnemyKind, GameState, PendingSpawn, WavePacket } from "../core/types.js";
import { pushLog } from "../state/createState.js";
import { awardWaveProgress } from "./progression.js";
import { spawnEnemy } from "./enemies.js";

function addPacket(packets: WavePacket[], kind: EnemyKind, count: number, cadence: number): void {
  if (count <= 0) {
    return;
  }

  packets.push({ kind, count, cadence });
}

export function buildWavePackets(stage: number, wave: number): WavePacket[] {
  const packets: WavePacket[] = [];
  const pressure = stage * 1.45 + wave;

  addPacket(packets, "grunt", 6 + Math.floor(pressure * 2.2), Math.max(0.27, 0.6 - pressure * 0.02));

  if (wave >= 2) {
    addPacket(
      packets,
      "runner",
      2 + Math.floor(pressure * 1.5),
      Math.max(0.22, 0.48 - pressure * 0.015),
    );
  }

  if (wave >= 3) {
    addPacket(packets, "tank", 1 + Math.floor((stage + wave) / 2), Math.max(0.55, 0.88 - pressure * 0.02));
    addPacket(
      packets,
      "splitter",
      1 + Math.floor((stage + wave) / 3),
      Math.max(0.48, 0.78 - pressure * 0.016),
    );
  }

  if (stage >= 2 && wave >= 3) {
    addPacket(
      packets,
      "bomber",
      1 + Math.floor((stage + wave) / 3),
      Math.max(0.42, 0.66 - pressure * 0.012),
    );
  }

  if (stage >= 3 && wave >= 4) {
    addPacket(
      packets,
      "shaman",
      1 + Math.floor((stage + wave) / 4),
      Math.max(0.68, 0.96 - pressure * 0.015),
    );
  }

  if (wave === 5) {
    addPacket(packets, "tank", 2 + stage, 0.74);
    addPacket(packets, "splitter", 2 + Math.floor(stage / 2), 0.7);
    addPacket(packets, "bomber", 2 + Math.floor(stage / 2), 0.64);

    if (stage >= 3) {
      addPacket(packets, "shaman", 1 + Math.floor(stage / 2), 0.84);
    }
  }

  return packets;
}

function packetsToPending(packets: WavePacket[]): PendingSpawn[] {
  return packets.map((packet) => ({
    kind: packet.kind,
    remaining: packet.count,
    cadence: packet.cadence,
    timer: 0,
  }));
}

export function startWave(state: GameState): void {
  if (state.phase !== "prep") {
    return;
  }

  lockClassSelection(state);

  state.wavePackets = buildWavePackets(state.stage, state.wave);
  state.pendingSpawns = packetsToPending(state.wavePackets);
  state.phase = "combat";
  state.waveGoalText = `Wave ${state.wave} / Stage ${state.stage}: defend the keep`;

  pushLog(state, `Wave ${state.wave} started.`);
}

export function updateWaveSpawning(state: GameState, dt: number): void {
  if (state.phase !== "combat") {
    return;
  }

  if (!state.pendingSpawns.length) {
    return;
  }

  const current = state.pendingSpawns[0];
  current.timer -= dt;

  while (current.remaining > 0 && current.timer <= 0) {
    spawnEnemy(state, current.kind);
    current.remaining -= 1;
    current.timer += current.cadence;
  }

  if (current.remaining <= 0) {
    state.pendingSpawns.shift();
    if (state.pendingSpawns[0]) {
      state.pendingSpawns[0].timer = Math.max(state.pendingSpawns[0].timer, 0.45);
    }
  }
}

function onWaveCleared(state: GameState): void {
  const clearReward = 38 + state.stage * 13 + state.wave * 12;
  state.gold += clearReward;
  awardWaveProgress(state);

  pushLog(state, `Wave ${state.wave} cleared. +${clearReward} gold.`);

  state.phase = "prep";
  state.pendingSpawns = [];
  state.wavePackets = [];

  if (state.wave >= state.wavesPerStage) {
    state.wave = 1;
    state.stage += 1;
  } else {
    state.wave += 1;
  }

  if (state.stage > state.maxStage) {
    state.phase = "victory";
    state.waveGoalText = "Victory: all stages cleared";
    pushLog(state, "All stages cleared. Victory.");
    return;
  }

  state.waveGoalText = `Prep: stage ${state.stage}, wave ${state.wave}. Build, then press Start Wave.`;
}

export function resolveWaveState(state: GameState): void {
  if (state.phase !== "combat") {
    return;
  }

  const hasSpawnsRemaining = state.pendingSpawns.length > 0;
  const hasEnemiesAlive = state.enemies.length > 0;

  if (!hasSpawnsRemaining && !hasEnemiesAlive) {
    onWaveCleared(state);
  }
}
