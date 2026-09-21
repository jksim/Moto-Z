// Keep in step with CATEGORIES in tools/taxonomy.py and the enum in
// src/content.config.ts.
export const CATEGORIES: { slug: string; label: string }[] = [
  { slug: 'audio', label: 'Audio' },
  { slug: 'power', label: 'Power' },
  { slug: 'camera', label: 'Camera' },
  { slug: 'projection', label: 'Projection & Printing' },
  { slug: 'style', label: 'Style & Protection' },
  { slug: 'connectivity', label: 'Connectivity & Mounting' },
  { slug: 'input', label: 'Gaming & Input' },
  { slug: 'development', label: 'Development' },
];

export function categoryLabel(slug: string): string {
  return CATEGORIES.find((c) => c.slug === slug)?.label ?? slug;
}
