import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import {
  meetingLabels,
  supportsCategories,
  supportsEventColour,
} from "./providerOptions.js";

describe("what each calendar supports", () => {
  it("offers colour on Google only, since Graph has no per-event colour", () => {
    assert.equal(supportsEventColour("google"), true);
    assert.equal(supportsEventColour("microsoft"), false);
  });

  it("offers categories on Outlook only", () => {
    assert.equal(supportsCategories("microsoft"), true);
    assert.equal(supportsCategories("google"), false);
  });

  it("names the right meeting type", () => {
    assert.match(meetingLabels("microsoft").checkbox, /Teams/);
    assert.match(meetingLabels("microsoft").generated, /Teams/);
    assert.match(meetingLabels("google").checkbox, /Google Meet/);
  });

  it("treats an unknown or missing provider as Google", () => {
    assert.equal(supportsEventColour(undefined), true);
    assert.match(meetingLabels(undefined).field, /Google Meet/);
  });
});
