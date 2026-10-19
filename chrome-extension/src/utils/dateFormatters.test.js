import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import { formatEndTime, formatTimeShort } from "./dateFormatters.js";

// Local times, so the test holds in any timezone.
const at = (month, day, hour) => new Date(2026, month, day, hour).toISOString();

describe("formatEndTime", () => {
  it("shows only the time when the event ends the day it starts", () => {
    const end = at(10, 3, 17);
    assert.equal(formatEndTime(at(10, 3, 9), end), formatTimeShort(end));
  });

  it("shows the date when the event runs on to a later day", () => {
    const text = formatEndTime(at(10, 3, 9), at(10, 5, 17));
    assert.match(text, /Thu, Nov 5/);
    assert.match(text, /5:00/);
  });

  it("is empty without an end", () => {
    assert.equal(formatEndTime(at(10, 3, 9), null), "");
  });
});
