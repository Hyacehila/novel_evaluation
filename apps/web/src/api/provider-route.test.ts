import { describe, expect, it } from "vitest";

import { isLocalWebRequest } from "@/api/provider-route";


describe("provider route guard", () => {
  it("accepts local requests without forwarding headers", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        origin: "http://127.0.0.1:13000",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(true);
  });

  it("accepts local requests carrying unrelated forwarded host metadata", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        origin: "http://127.0.0.1:13000",
        "x-forwarded-host": "127.0.0.1:13000",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(true);
  });

  it("accepts local requests carrying loopback forwarded client metadata", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        origin: "http://127.0.0.1:13000",
        "x-forwarded-for": "127.0.0.1",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(true);
  });

  it("accepts local requests carrying IPv6 forwarded metadata with ports", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        referer: "http://localhost:13000/tasks/new",
        forwarded: 'for="[::1]:43124";proto=http;host=127.0.0.1:13000',
        "x-real-ip": "[::1]:43124",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(true);
  });

  it("accepts local requests carrying IPv4-mapped IPv6 forwarded metadata", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        origin: "http://127.0.0.1:13000",
        "x-forwarded-for": "::ffff:127.0.0.1",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(true);
  });

  it("rejects requests carrying non-loopback forwarded client metadata", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        origin: "http://127.0.0.1:13000",
        "x-forwarded-for": "203.0.113.8",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(false);
  });

  it("rejects requests missing browser origin metadata", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(false);
  });

  it("rejects remote origins", () => {
    const request = new Request("http://127.0.0.1:13000/api/provider-status/runtime-key", {
      method: "POST",
      headers: {
        origin: "https://example.com",
      },
      body: JSON.stringify({ apiKey: "sk-test" }),
    });

    expect(isLocalWebRequest(request)).toBe(false);
  });
});
