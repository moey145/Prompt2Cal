import { strict as assert } from "node:assert";
import { describe, it } from "node:test";
import {
  PARSE_TIMEOUT_MS,
  PREVIEW_MAX_AGE_MS,
  parseJobState,
  previewToRestore,
  previewToSave,
} from "./parseJob.js";

const now = 1_000_000_000;

describe("parseJobState", () => {
  it("reads each stage of a job", () => {
    assert.equal(parseJobState(null, now), "none");
    assert.equal(parseJobState({ status: "pending", startedAt: now - 1000 }, now), "pending");
    assert.equal(parseJobState({ status: "done", response: { success: true } }, now), "done");
    assert.equal(parseJobState({ status: "error", error: "x" }, now), "error");
  });

  it("treats a job pending for too long as cut off", () => {
    const job = { status: "pending", startedAt: now - PARSE_TIMEOUT_MS - 1 };
    assert.equal(parseJobState(job, now), "stalled");
  });

  it("ignores a finished job with no response", () => {
    assert.equal(parseJobState({ status: "done" }, now), "none");
  });
});

describe("previewToSave", () => {
  it("saves the single preview on screen", () => {
    const saved = previewToSave({ showParsedEvent: true, parsedEvent: { title: "Lunch" } }, now);
    assert.deepEqual(saved, { kind: "single", event: { title: "Lunch" }, savedAt: now });
  });

  it("saves a list of events", () => {
    const saved = previewToSave({ showBulkEvents: true, parsedEvents: [{ title: "A" }] }, now);
    assert.equal(saved.kind, "bulk");
  });

  it("saves nothing once the preview is dismissed", () => {
    assert.equal(previewToSave({ showParsedEvent: false, parsedEvent: { title: "Lunch" } }, now), null);
    assert.equal(previewToSave({ showBulkEvents: true, parsedEvents: [] }, now), null);
  });
});

describe("previewToRestore", () => {
  it("brings back a recent preview", () => {
    const saved = { kind: "single", event: { title: "Lunch" }, savedAt: now - 1000 };
    assert.equal(previewToRestore(saved, now), saved);
  });

  it("drops an old or empty one", () => {
    assert.equal(previewToRestore({ kind: "single", event: {}, savedAt: now - PREVIEW_MAX_AGE_MS - 1 }, now), null);
    assert.equal(previewToRestore({ kind: "bulk", events: [], savedAt: now }, now), null);
    assert.equal(previewToRestore(undefined, now), null);
  });
});
