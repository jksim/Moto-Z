// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://jksim.github.io',
  base: '/Moto-Z',
  trailingSlash: 'always',
  output: 'static',
  build: { format: 'directory' },
  integrations: [sitemap()],
});
