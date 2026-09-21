import { defineCollection, reference, z } from 'astro:content';
import { file } from 'astro/loaders';

const spec = z.object({ label: z.string(), value: z.string() });
const feature = z.object({ title: z.string(), body: z.string() });
const image = z.object({
  key: z.string(),
  role: z.enum(['hero', 'feature', 'gallery', 'spec', 'logo']),
  width: z.number(),
  height: z.number(),
  focusX: z.number().default(0.5),
  focusY: z.number().default(0.5),
  bg: z.string().default(''),
});
const facets = z.object({
  weightG: z.number().optional(),
  dimensionsMm: z.string().optional(),
  batteryMah: z.number().optional(),
  displayIn: z.number().optional(),
});

const award = z.object({
  award: z.string(),
  year: z.number().nullable().default(null),
  tier: z.string().default(''),
  jury: z.string().default(''),
  url: z.string(),
});

const mods = defineCollection({
  loader: file('data/mods.json'),
  schema: z.object({
    slug: z.string(),
    name: z.string(),
    brand: z.string(),
    year: z.number(),
    // Keep in step with CATEGORIES in tools/taxonomy.py and src/lib/catalogue.ts.
    category: z.enum(['audio', 'power', 'camera', 'projection', 'style',
                      'connectivity', 'input', 'development']),
    categorySecondary: z.array(z.string()),
    tagline: z.string(),
    summary: z.string(),
    details: z.string().default(''),
    features: z.array(feature),
    specs: z.array(spec).min(1),
    facets,
    compatibilityRaw: z.string(),
    compatibleDevices: z.array(reference('phones')).min(1),
    fit: z.enum(['universal', 'per-model']),
    relatedDocs: z.array(z.object({ title: z.string(), url: z.string() })),
    timeline: z.array(z.object({ date: z.string(), event: z.string() })).default([]),
    awards: z.array(award).default([]),
    images: z.array(image),
    coverKey: z.string().default(''),
    sources: z.array(z.string()).min(1),
  }),
});

const phones = defineCollection({
  loader: file('data/phones.json'),
  schema: z.object({
    slug: z.string(),
    name: z.string(),
    family: z.string(),
    generation: z.number(),
    year: z.number(),
    variants: z.array(z.object({
      slug: z.string(), name: z.string(), carrier: z.string(),
    })),
    tagline: z.string(),
    summary: z.string(),
    features: z.array(feature),
    specs: z.array(spec).min(1),
    facets,
    compatibleMods: z.array(reference('mods')),
    awards: z.array(award).default([]),
    images: z.array(image),
    coverKey: z.string().default(''),
    sources: z.array(z.string()).min(1),
  }),
});

export const collections = { mods, phones };
