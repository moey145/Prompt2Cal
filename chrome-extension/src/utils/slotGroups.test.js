import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import { dayLabel, groupSlotsByDay } from "./slotGroups.js";

// Local times, so the test holds in any timezone.
const now = new Date(2026, 9, 1, 8, 0);
const at = (day, hour, minute = 0) => new Date(2026, 9, day, hour, minute).toISOString();

describe("dayLabel", () => {
  it("names today and tomorrow", () => {
    assert.equal(dayLabel(new Date(2026, 9, 1, 15, 0), now), "Today");
    assert.equal(dayLabel(new Date(2026, 9, 2, 9, 0), now), "Tomorrow");
  });

  it("gives a short date further out", () => {
    const label = dayLabel(new Date(2026, 9, 5, 9, 0), now);
    assert.notEqual(label, "Today");
    assert.notEqual(label, "Tomorrow");
    assert.match(label, /5/);
  });
});

describe("groupSlotsByDay", () => {
  it("keeps slots in order under one heading per day", () => {
    const slots = [
      { start: at(1, 9) },
      { start: at(1, 10, 30) },
      { start: at(2, 9) },
    ];
    const groups = groupSlotsByDay(slots, now);
    assert.deepEqual(groups.map((g) => g.label), ["Today", "Tomorrow"]);
    assert.equal(groups[0].slots.length, 2);
    assert.equal(groups[1].slots[0].start, slots[2].start);
    assert.ok(groups[0].slots[0].time);
  });

  it("returns nothing for no slots", () => {
    assert.deepEqual(groupSlotsByDay([], now), []);
  });
});
