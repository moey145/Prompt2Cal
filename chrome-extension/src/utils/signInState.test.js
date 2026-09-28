import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import {
  SIGN_IN_TIMEOUT_MS,
  isIssuedSession,
  pendingSignInProvider,
} from "./signInState.js";

const issued = "s_" + "a".repeat(43);

describe("isIssuedSession", () => {
  it("accepts a session the backend issued", () => {
    assert.equal(isIssuedSession(issued), true);
  });

  it("rejects ids older versions of the extension made up, and junk", () => {
    for (const value of ["user_ngrj32xjn", "", null, undefined, "s_short", "../token", 42]) {
      assert.equal(isIssuedSession(value), false, `${value} must be rejected`);
    }
  });
});

describe("pendingSignInProvider", () => {
  const now = 1_000_000;

  it("reports the provider whose sign-in is still open", () => {
    assert.equal(
      pendingSignInProvider({ waitingForAuth: "google", authStartedAt: now - 1000 }, now),
      "google"
    );
    assert.equal(
      pendingSignInProvider({ waitingForAuth: "microsoft", authStartedAt: now - 1000 }, now),
      "microsoft"
    );
  });

  it("reports nothing when no sign-in is running", () => {
    assert.equal(pendingSignInProvider({}, now), null);
    assert.equal(pendingSignInProvider(null, now), null);
  });

  it("gives up on a sign-in left open too long, so a button cannot stick", () => {
    const stale = { waitingForAuth: "google", authStartedAt: now - SIGN_IN_TIMEOUT_MS - 1 };
    assert.equal(pendingSignInProvider(stale, now), null);
  });

  it("treats a missing start time as stale", () => {
    assert.equal(pendingSignInProvider({ waitingForAuth: "google" }, now), null);
  });

  it("falls back to Google for an unrecognised provider", () => {
    assert.equal(
      pendingSignInProvider({ waitingForAuth: "true", authStartedAt: now }, now),
      "google"
    );
  });
});
