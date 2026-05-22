const TOKEN_KEY = "rtp_access_token";
const ORG_SLUG_KEY = "rtp_org_slug";

export function getStoredToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function getStoredOrgSlug(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(ORG_SLUG_KEY) ?? "";
}

export function setStoredAuth(token: string, orgSlug?: string) {
  localStorage.setItem(TOKEN_KEY, token);
  if (orgSlug) localStorage.setItem(ORG_SLUG_KEY, orgSlug);
}

export function clearStoredAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ORG_SLUG_KEY);
}
