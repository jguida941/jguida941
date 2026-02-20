// === Input Controller (Mouse / Touch / Keyboard / UI Commands) ===

import { distanceSquared } from "../core/math.js";
import type {
  BuildingKind,
  HeroClass,
  PlayerCommand,
  SpellKind,
  TowerKind,
  TowerSlot,
  UpgradeKind,
  Vec2,
} from "../core/types.js";

export interface InputBindings {
  canvas: HTMLCanvasElement;
  startWaveButton: HTMLButtonElement;
  classButtons: Record<HeroClass, HTMLButtonElement>;
  towerButtons: Record<TowerKind, HTMLButtonElement>;
  buildingButtons: Record<BuildingKind, HTMLButtonElement>;
  spellButtons: Record<SpellKind, HTMLButtonElement>;
  upgradeButtons: Record<UpgradeKind, HTMLButtonElement>;
}

export type CommandEnqueue = (command: PlayerCommand) => void;

export type TowerSlotSnapshot = () => TowerSlot[];

function canvasPointFromPointer(canvas: HTMLCanvasElement, event: PointerEvent): Vec2 {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY,
  };
}

function findClickedSlot(point: Vec2, slots: TowerSlot[]): number | null {
  for (const slot of slots) {
    if (distanceSquared(point, slot.position) <= 20 * 20) {
      return slot.id;
    }
  }
  return null;
}

export function bindInput(
  bindings: InputBindings,
  enqueue: CommandEnqueue,
  getTowerSlots: TowerSlotSnapshot,
): () => void {
  const disposers: Array<() => void> = [];

  const onStartWaveClick = () => enqueue({ type: "start_wave" });
  bindings.startWaveButton.addEventListener("click", onStartWaveClick);
  disposers.push(() => bindings.startWaveButton.removeEventListener("click", onStartWaveClick));

  for (const [heroClass, button] of Object.entries(bindings.classButtons) as Array<
    [HeroClass, HTMLButtonElement]
  >) {
    const handler = () => enqueue({ type: "select_class", heroClass });
    button.addEventListener("click", handler);
    disposers.push(() => button.removeEventListener("click", handler));
  }

  for (const [towerKind, button] of Object.entries(bindings.towerButtons) as Array<
    [TowerKind, HTMLButtonElement]
  >) {
    const handler = () => enqueue({ type: "select_tower", tower: towerKind });
    button.addEventListener("click", handler);
    disposers.push(() => button.removeEventListener("click", handler));
  }

  for (const [buildingKind, button] of Object.entries(bindings.buildingButtons) as Array<
    [BuildingKind, HTMLButtonElement]
  >) {
    const handler = () => enqueue({ type: "select_building", building: buildingKind });
    button.addEventListener("click", handler);
    disposers.push(() => button.removeEventListener("click", handler));
  }

  for (const [spellKind, button] of Object.entries(bindings.spellButtons) as Array<
    [SpellKind, HTMLButtonElement]
  >) {
    const handler = () => enqueue({ type: "cast_spell", spell: spellKind });
    button.addEventListener("click", handler);
    disposers.push(() => button.removeEventListener("click", handler));
  }

  for (const [upgradeKind, button] of Object.entries(bindings.upgradeButtons) as Array<
    [UpgradeKind, HTMLButtonElement]
  >) {
    const handler = () => enqueue({ type: "buy_upgrade", upgrade: upgradeKind });
    button.addEventListener("click", handler);
    disposers.push(() => button.removeEventListener("click", handler));
  }

  const onCanvasPointerDown = (event: PointerEvent) => {
    const point = canvasPointFromPointer(bindings.canvas, event);
    const slotId = findClickedSlot(point, getTowerSlots());
    if (slotId !== null) {
      enqueue({ type: "place_selected", slotId });
    }
  };

  bindings.canvas.addEventListener("pointerdown", onCanvasPointerDown);
  disposers.push(() => bindings.canvas.removeEventListener("pointerdown", onCanvasPointerDown));

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.code === "Space") {
      event.preventDefault();
      enqueue({ type: "start_wave" });
      return;
    }

    const classByKey: Record<string, HeroClass> = {
      KeyA: "warlord",
      KeyS: "arcanist",
      KeyD: "architect",
    };

    const towerByKey: Record<string, TowerKind> = {
      Digit1: "cannon",
      Digit2: "rapid",
      Digit3: "sniper",
      Digit4: "frost",
    };

    const buildingByKey: Record<string, BuildingKind> = {
      Digit5: "gold_mine",
      Digit6: "barracks",
      Digit7: "spell_lab",
    };

    const spellByKey: Record<string, SpellKind> = {
      KeyZ: "meteor",
      KeyX: "frost_nova",
      KeyC: "healing_aura",
    };

    const upgradeByKey: Record<string, UpgradeKind> = {
      KeyQ: "damage",
      KeyW: "range",
      KeyE: "fire_rate",
      KeyR: "economy",
    };

    if (classByKey[event.code]) {
      enqueue({ type: "select_class", heroClass: classByKey[event.code] });
      return;
    }

    if (towerByKey[event.code]) {
      enqueue({ type: "select_tower", tower: towerByKey[event.code] });
      return;
    }

    if (buildingByKey[event.code]) {
      enqueue({ type: "select_building", building: buildingByKey[event.code] });
      return;
    }

    if (spellByKey[event.code]) {
      enqueue({ type: "cast_spell", spell: spellByKey[event.code] });
      return;
    }

    if (upgradeByKey[event.code]) {
      enqueue({ type: "buy_upgrade", upgrade: upgradeByKey[event.code] });
    }
  };

  window.addEventListener("keydown", onKeyDown);
  disposers.push(() => window.removeEventListener("keydown", onKeyDown));

  return () => {
    for (const dispose of disposers) {
      dispose();
    }
  };
}
