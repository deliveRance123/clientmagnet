/**
 * Intelligent API Base URL resolver with automatic Render detection,
 * multi-candidate dynamic failover, runtime overrides, IPv4 fallback,
 * and self-healing resilience against connection failures.
 */

const CANDIDATE_RENDER_BACKENDS = [
  "https://client-magnet.onrender.com/api/v1",
  "https://clientmagnet.onrender.com/api/v1",
  "https://client-magnet-backend.onrender.com/api/v1",
  "https://clientmagnet-backend.onrender.com/api/v1",
  "https://clientmagnet-api.onrender.com/api/v1",
];

let cachedWorkingBackend: string | null = null;

export function getApiBase(): string {
  // 1. In-memory cached working backend
  if (cachedWorkingBackend) {
    return cachedWorkingBackend;
  }

  // 2. Explicit Environment Variable (Render / Production)
  if (process.env.NEXT_PUBLIC_API_URL) {
    let url = process.env.NEXT_PUBLIC_API_URL.trim();
    if (!url.endsWith("/api/v1")) {
      url = url.replace(/\/+$/, "") + "/api/v1";
    }
    return url;
  }

  // 3. Client-side dynamic host inspection & localStorage
  if (typeof window !== "undefined") {
    // Check for explicit query param override e.g. ?backend=https://...
    try {
      const searchParams = new URLSearchParams(window.location.search);
      const queryBackend = searchParams.get("backend");
      if (queryBackend) {
        let url = queryBackend.trim();
        if (!url.endsWith("/api/v1")) url = url.replace(/\/+$/, "") + "/api/v1";
        localStorage.setItem("cm_backend_url", url);
        cachedWorkingBackend = url;
        return url;
      }
    } catch (e) {}

    // Check for user-saved runtime config override
    const customApiUrl =
      localStorage.getItem("cm_backend_url") ||
      localStorage.getItem("cm_working_backend") ||
      (window as any).__API_URL__;

    if (customApiUrl) {
      let url = String(customApiUrl).trim();
      if (!url.endsWith("/api/v1")) {
        url = url.replace(/\/+$/, "") + "/api/v1";
      }
      return url;
    }

    const hostname = window.location.hostname;

    // Direct IPv4 loopback or localhost
    if (hostname === "127.0.0.1" || hostname === "localhost") {
      return "http://127.0.0.1:8000/api/v1";
    }

    // If deployed on Render
    if (hostname.includes("onrender.com")) {
      return CANDIDATE_RENDER_BACKENDS[0];
    }
  }

  // 4. Default local development backend
  return "http://127.0.0.1:8000/api/v1";
}

/**
 * Resilient fetcher with automatic IPv4 fallback, multi-backend failover,
 * and retry on network drop or 404 / 503 from dormant Render instances.
 */
export async function resilientFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const currentBase = getApiBase();

  // If absolute URL was passed, fetch directly
  if (endpoint.startsWith("http")) {
    return await fetch(endpoint, options);
  }

  const primaryUrl = `${currentBase}${cleanEndpoint}`;

  try {
    const res = await fetch(primaryUrl, options);
    // If successful or client error (like 400/401/422 with JSON detail from backend API), return it
    if (res.ok || (res.status !== 404 && res.status !== 502 && res.status !== 503)) {
      cachedWorkingBackend = currentBase;
      if (typeof window !== "undefined") {
        localStorage.setItem("cm_working_backend", currentBase);
      }
      return res;
    }
    // If 404/502/503 on production, try failover candidates
    if (typeof window !== "undefined" && window.location.hostname.includes("onrender.com")) {
      return await tryFailoverCandidates(cleanEndpoint, options, currentBase);
    }
    return res;
  } catch (err) {
    // Localhost IPv6 fallback
    if (primaryUrl.includes("localhost:8000")) {
      const fallbackUrl = primaryUrl.replace("localhost:8000", "127.0.0.1:8000");
      try {
        return await fetch(fallbackUrl, options);
      } catch (e) {}
    }

    // In production on Render, try failover candidates
    if (typeof window !== "undefined" && window.location.hostname.includes("onrender.com")) {
      try {
        return await tryFailoverCandidates(cleanEndpoint, options, currentBase);
      } catch (failoverErr) {
        throw err;
      }
    }
    throw err;
  }
}

/**
 * Iterates through candidate backends until a responsive one is found
 */
async function tryFailoverCandidates(
  cleanEndpoint: string,
  options: RequestInit,
  failedBase: string
): Promise<Response> {
  const candidates = CANDIDATE_RENDER_BACKENDS.filter((c) => c !== failedBase);

  for (const candidate of candidates) {
    const testUrl = `${candidate}${cleanEndpoint}`;
    try {
      const testRes = await fetch(testUrl, options);
      if (testRes.ok || (testRes.status !== 404 && testRes.status !== 502 && testRes.status !== 503)) {
        cachedWorkingBackend = candidate;
        if (typeof window !== "undefined") {
          localStorage.setItem("cm_working_backend", candidate);
        }
        return testRes;
      }
    } catch (e) {
      // Continue trying next candidate
    }
  }

  throw new Error("Unable to connect to any backend service instance.");
}
