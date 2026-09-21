#!/usr/bin/env node
// Fails the build on a local link that does not resolve, and on any
// root-relative link missing the GitHub Pages base path.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';

const dist = resolve(process.argv[2] ?? 'dist');
const config = readFileSync('astro.config.mjs', 'utf8');
const base = (config.match(/base:\s*'([^']*)'/) ?? [, ''])[1].replace(/\/$/, '');

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}

const pages = walk(dist).filter((p) => p.endsWith('.html'));
const problems = [];

for (const page of pages) {
  const html = readFileSync(page, 'utf8');
  const refs = [...html.matchAll(/(?:href|src)="([^"]+)"/g)].map((m) => m[1]);
  for (const ref of refs) {
    if (/^(https?:|mailto:|data:|#|\/\/)/.test(ref)) continue;
    const clean = ref.split(/[?#]/)[0];
    if (!clean) continue;

    if (clean.startsWith('/')) {
      if (base && !clean.startsWith(base + '/') && clean !== base) {
        problems.push(`${page}: "${ref}" is missing the base path "${base}"`);
        continue;
      }
      const rel = base ? clean.slice(base.length) : clean;
      const target = join(dist, rel);
      if (!existsSync(target) && !existsSync(join(target, 'index.html'))) {
        problems.push(`${page}: "${ref}" does not resolve`);
      }
    } else {
      const target = resolve(dirname(page), clean);
      if (!existsSync(target) && !existsSync(join(target, 'index.html'))) {
        problems.push(`${page}: "${ref}" does not resolve`);
      }
    }
  }
}

console.log(`checked ${pages.length} pages`);
if (problems.length) {
  for (const p of problems.slice(0, 40)) console.error('  ' + p);
  console.error(`${problems.length} broken link(s)`);
  process.exit(1);
}
console.log('links ok');
