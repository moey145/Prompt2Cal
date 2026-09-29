import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import {
  fieldsForEnd,
  fieldsForStart,
  formatDuration,
  toInputValue,
  validateEvent,
} from "./eventEditing.js";

// Local times, so the tests hold in any timezone.
const local = (day, hour, minute = 0) => new Date(2026, 9, day, hour, minute).toISOString();

describe("fieldsForStart", () => {
  it("moves the end with the start, keeping the edited length", () => {
    const event = { start_time: local(1, 9), end_time: local(1, 10, 30), duration_minutes: 60 };
    const fields = fieldsForStart(event, toInputValue(local(1, 14)));
    assert.equal(fields.start_time, local(1, 14));
    assert.equal(fields.end_time, local(1, 15, 30));
    assert.equal(fields.duration_minutes, 90);
  });

  it("falls back to the duration when there is no end yet", () => {
    const fields = fieldsForStart({ duration_minutes: 45 }, toInputValue(local(1, 9)));
    assert.equal(fields.end_time, local(1, 9, 45));
  });

  it("ignores a half-typed value", () => {
    assert.equal(fieldsForStart({}, ""), null);
  });
});

describe("fieldsForEnd", () => {
  it("updates the length with the end", () => {
    const fields = fieldsForEnd({ start_time: local(1, 9) }, toInputValue(local(1, 11)));
    assert.equal(fields.duration_minutes, 120);
  });

  it("leaves the length alone for an end before the start", () => {
    const fields = fieldsForEnd({ start_time: local(1, 9) }, toInputValue(local(1, 8)));
    assert.equal(fields.duration_minutes, undefined);
  });
});

describe("formatDuration", () => {
  it("reads naturally", () => {
    assert.equal(formatDuration(45), "45 min");
    assert.equal(formatDuration(60), "1 hr");
    assert.equal(formatDuration(90), "1 hr 30 min");
    assert.equal(formatDuration(2880), "2 days");
    assert.equal(formatDuration(0), "");
  });
});

describe("validateEvent", () => {
  const valid = { title: "Lunch", start_time: local(1, 12), end_time: local(1, 13) };

  it("accepts a complete event", () => {
    assert.deepEqual(validateEvent(valid), {});
  });

  it("needs a title and a start", () => {
    const errors = validateEvent({ title: "  " });
    assert.ok(errors.title);
    assert.ok(errors.start_time);
  });

  it("rejects an end at or before the start", () => {
    assert.ok(validateEvent({ ...valid, end_time: local(1, 12) }).end_time);
  });

  it("rejects a series that ends before it starts", () => {
    assert.ok(validateEvent({ ...valid, recurrence_type: "weekly", end_date: "2026-09-01" }).end_date);
    assert.deepEqual(validateEvent({ ...valid, recurrence_type: "weekly", end_date: "2026-10-01" }), {});
  });
});

describe("toInputValue", () => {
  it("is empty for a missing time rather than 1970", () => {
    assert.equal(toInputValue(null), "");
    assert.equal(toInputValue("not a date"), "");
  });
});
