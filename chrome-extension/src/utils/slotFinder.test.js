import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import { slotFinderSupported, slotSearchErrorMessage } from "./slotFinder.js";

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
