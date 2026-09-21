// Astro does not rewrite hand-written root-relative hrefs. Every internal link
// goes through here so the GitHub Pages project sub-path is always applied.
const BASE = import.meta.env.BASE_URL;

export function href(path: string): string {
  const joined = `${BASE}/${path}`.replace(/\/{2,}/g, '/');
  return joined.endsWith('/') || joined.includes('.') ? joined : `${joined}/`;
}

export function asset(path: string): string {
  return `${BASE}/${path}`.replace(/\/{2,}/g, '/');
}
