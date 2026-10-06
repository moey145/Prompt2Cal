import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import {
  DEFAULT_SLOT_HOURS,
  formatHour,
  slotFinderSupported,
  slotSearchErrorMessage,
  validSlotHours,
} from "./slotFinder.js";

describe("slotFinderSupported", () => {
  it("follows the backend's provider list", () => {
    const health = { status: "healthy", slot_finder_providers: ["google", "microsoft"] };
    assert.equal(slotFinderSupported(health, "microsoft"), true);
    assert.equal(slotFinderSupported(health, "google"), true);
  });

  it("offers only Google on a backend without the list", () => {
    const health = { status: "healthy" };
    assert.equal(slotFinderSupported(health, "google"), true);
    assert.equal(slotFinderSupported(health, "microsoft"), false);
  });

  it("is off with no provider", () => {
    assert.equal(slotFinderSupported({ slot_finder_providers: ["google"] }, null), false);
  });
});

describe("slotSearchErrorMessage", () => {
  const withStatus = (status, message) => Object.assign(new Error(message), { status });

  it("passes on the backend's reconnect message", () => {
    const error = withStatus(409, "Connect Outlook Calendar in Settings to find free slots.");
    assert.equal(slotSearchErrorMessage(error, "microsoft"), error.message);
  });

  it("names the provider when the session is gone", () => {
    assert.equal(
      slotSearchErrorMessage(withStatus(401, "Not signed in."), "google"),
      "Connect Google Calendar in Settings to find free slots."
    );
  });

  it("never shows a wrapped technical error", () => {
    const raw = withStatus(
      400,
      "Failed to find meeting slots: Failed to find available slots: Google Calendar is not connected."
    );
    assert.equal(slotSearchErrorMessage(raw, "google"), "Couldn't check your calendar. Try again in a moment.");
    assert.equal(slotSearchErrorMessage(new TypeError("Failed to fetch"), "google"), "Couldn't check your calendar. Try again in a moment.");
  });
});

describe("formatHour", () => {
  it("reads like a clock", () => {
    assert.equal(formatHour(0), "midnight");
    assert.equal(formatHour(9), "9am");
    assert.equal(formatHour(12), "noon");
    assert.equal(formatHour(17), "5pm");
    assert.equal(formatHour(24), "midnight");
  });
});

describe("validSlotHours", () => {
  it("keeps sensible saved hours", () => {
    assert.deepEqual(validSlotHours([7, 22]), [7, 22]);
    assert.deepEqual(validSlotHours([18, 24]), [18, 24]);
  });

  it("falls back to 9 to 5 for anything else", () => {
    for (const bad of [undefined, [17, 9], [9, 25], ["9", 17], [9]]) {
      assert.deepEqual(validSlotHours(bad), DEFAULT_SLOT_HOURS);
    }
  });
});
