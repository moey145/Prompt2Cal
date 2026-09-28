import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import {
  defaultRecurrenceEndDate,
  fieldsForEndMode,
  fieldsForRecurrenceType,
  intervalUnitLabel,
  isRecurring,
  recurrenceEndMode,
} from "./recurrence.js";

describe("isRecurring", () => {
  it("treats none and missing as one-off", () => {
    assert.equal(isRecurring({ recurrence_type: "weekly" }), true);
    assert.equal(isRecurring({ recurrence_type: "none" }), false);
    assert.equal(isRecurring({}), false);
    assert.equal(isRecurring(null), false);
  });
});

describe("recurrenceEndMode", () => {
  it("reads the ending the event describes", () => {
    assert.equal(recurrenceEndMode({ recurrence_count: 3 }), "count");
    assert.equal(recurrenceEndMode({ end_date: "2026-12-01" }), "date");
    assert.equal(recurrenceEndMode({}), "never");
  });
});

describe("fieldsForRecurrenceType", () => {
  it("clears series-only settings when the repeat is turned off", () => {
    assert.deepEqual(fieldsForRecurrenceType("none"), {
      recurrence_type: "none",
      recurrence_count: null,
      end_date: null,
      recurrence_interval: 1,
    });
  });

  it("keeps the rest when a pattern is chosen", () => {
    assert.deepEqual(fieldsForRecurrenceType("monthly"), { recurrence_type: "monthly" });
  });
});

describe("fieldsForEndMode", () => {
  it("never: clears both endings", () => {
    assert.deepEqual(fieldsForEndMode("never", { recurrence_count: 4 }), {
      recurrence_count: null,
      end_date: null,
    });
  });

  it("count: keeps an existing count, else suggests one", () => {
    assert.equal(fieldsForEndMode("count", { recurrence_count: 4 }).recurrence_count, 4);
    assert.equal(fieldsForEndMode("count", {}).recurrence_count, 5);
    assert.equal(fieldsForEndMode("count", {}).end_date, null);
  });

  it("date: keeps an existing date, else suggests three months out", () => {
    assert.equal(
      fieldsForEndMode("date", { end_date: "2026-12-24" }).end_date,
      "2026-12-24"
    );
    // The date is worked out in the viewer's own timezone, so check the gap
    // rather than a fixed day.
    const start = "2026-10-01T10:00:00+10:00";
    const suggested = fieldsForEndMode("date", { start_time: start });
    const daysAhead =
      (new Date(suggested.end_date) - new Date(start)) / (1000 * 60 * 60 * 24);
    assert.ok(daysAhead > 88 && daysAhead < 95, `about three months, got ${daysAhead}`);
    assert.equal(suggested.recurrence_count, null);
  });

  it("the two endings are never set at once", () => {
    for (const mode of ["never", "count", "date"]) {
      const fields = fieldsForEndMode(mode, { recurrence_count: 2, end_date: "2026-12-01" });
      assert.ok(
        fields.recurrence_count === null || fields.end_date === null,
        `${mode} must not set both endings`
      );
    }
  });
});

describe("intervalUnitLabel", () => {
  it("names the unit for each pattern", () => {
    assert.equal(intervalUnitLabel("weekly"), "week(s)");
    assert.equal(intervalUnitLabel("monthly"), "month(s)");
    assert.equal(intervalUnitLabel("none"), undefined);
  });
});

describe("defaultRecurrenceEndDate", () => {
  it("is three months after the start, as a plain date", () => {
    assert.equal(defaultRecurrenceEndDate("2026-01-15T09:00:00Z"), "2026-04-15");
  });

  it("copes with a missing or unreadable start", () => {
    assert.match(defaultRecurrenceEndDate(null), /^\d{4}-\d{2}-\d{2}$/);
    assert.match(defaultRecurrenceEndDate("nonsense"), /^\d{4}-\d{2}-\d{2}$/);
  });
});
