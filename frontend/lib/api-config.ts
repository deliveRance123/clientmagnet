/**
 * Intelligent API Base URL resolver with automatic Render detection,
 * IPv4 fallback, and resilience against connection failures.
 */

export function getApiBase(): string {
  // 1. Explicit Environment Variable (Render / Production)
  if (process.env.NEXT_PUBLIC_API_URL) {
    let url = process.env.NEXT_PUBLIC_API_URL.trim();
    if (!url.endsWith("/api/v1")) {
      url = url.replace(/\/+$/, "") + "/api/v1";
    }
    return url;
  }

  // 2. Client-side dynamic host inspection
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;

    // If deployed on Render
    if (hostname.includes("onrender.com")) {
      return "https://clientmagnet-ruxv.onrender.com/api/v1";
    }

    // Direct IPv4 loopback
    if (hostname === "127.0.0.1") {
      return "http://127.0.0.1:8000/api/v1";
    }
  }

  // 3. Default local development backend
  return "http://localhost:8000/api/v1";
}

/**
 * Resilient fetcher with automatic IPv4 fallback and retry on network drop
 */
export async function resilientFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const base = getApiBase();
  const url = endpoint.startsWith("http") ? endpoint : `${base}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  try {
    return await fetch(url, options);
  } catch (err) {
    // If localhost failed on Windows (IPv6 ::1 issue), fallback to 127.0.0.1 immediately
    if (url.includes("localhost:8000")) {
      const fallbackUrl = url.replace("localhost:8000", "127.0.0.1:8000");
      try {
        return await fetch(fallbackUrl, options);
      } catch (fallbackErr) {
        throw err;
      }
    }
    throw err;
  }
}
