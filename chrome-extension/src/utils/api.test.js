import { strict as assert } from "node:assert";
import { afterEach, describe, it } from "node:test";
import { makeApiCall } from "./api.js";

const calls = [];

const stubFetch = (response) => {
  calls.length = 0;
  global.fetch = async (url, options) => {
    calls.push({ url, options });
    return response;
  };
};

afterEach(() => {
  delete global.fetch;
});

describe("makeApiCall", () => {
  it("leaves unset params out of the query string", async () => {
    stubFetch({ ok: true, json: async () => ({ success: true }) });

    await makeApiCall("/auth/status", {
      method: "GET",
      params: { user_id: null, provider: "google", calendar_id: undefined },
    });

    const { url } = calls[0];
    assert.ok(url.includes("provider=google"));
    assert.ok(!url.includes("user_id"), "an unset session must not be sent");
    assert.ok(!url.includes("null"));
  });

  it("sends a plain request when there are no params", async () => {
    stubFetch({ ok: true, json: async () => ({ status: "healthy" }) });

    const body = await makeApiCall("/health");

    assert.ok(calls[0].url.endsWith("/health"));
    assert.equal(calls[0].options.headers["Content-Type"], "application/json");
    assert.deepEqual(body, { status: "healthy" });
  });

  it("raises the server's message when a request fails", async () => {
    stubFetch({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({ detail: "Not signed in. Please connect your calendar." }),
    });

    await assert.rejects(makeApiCall("/calendars"), /Not signed in/);
  });

  it("falls back to the status code when there is no message", async () => {
    stubFetch({
      ok: false,
      status: 429,
      statusText: "Too Many Requests",
      json: async () => {
        throw new Error("no body");
      },
    });

    await assert.rejects(makeApiCall("/create_event"), /429/);
  });
});
