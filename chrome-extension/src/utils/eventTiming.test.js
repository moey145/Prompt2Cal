import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import { startsInThePast } from "./eventTiming.js";

const now = new Date("2026-10-01T12:00:00+10:00");

describe("startsInThePast", () => {
  it("flags a one-off event whose time has gone", () => {
    assert.equal(startsInThePast({ start_time: "2026-10-01T10:00:00+10:00" }, now), true);
  });

  it("leaves a future event alone", () => {
    assert.equal(startsInThePast({ start_time: "2026-10-01T14:00:00+10:00" }, now), false);
  });

  it("exempts a series, which often starts before today", () => {
    const event = { start_time: "2026-09-01T10:00:00+10:00", recurrence_type: "weekly" };
    assert.equal(startsInThePast(event, now), false);
  });

  it("treats an explicit 'none' as a one-off", () => {
    const event = { start_time: "2026-10-01T10:00:00+10:00", recurrence_type: "none" };
    assert.equal(startsInThePast(event, now), true);
  });

  it("says nothing when there is no usable start time", () => {
    assert.equal(startsInThePast({}, now), false);
    assert.equal(startsInThePast(null, now), false);
    assert.equal(startsInThePast({ start_time: "not a date" }, now), false);
  });
});
