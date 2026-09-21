// Images are addressed by key so the JSON never has to know about file paths.
const files = import.meta.glob<{ default: ImageMetadata }>(
  '/src/assets/products/**/*.{jpg,jpeg,png,gif,webp,svg}',
  { eager: true },
);

const byKey = new Map<string, ImageMetadata>();
for (const [path, mod] of Object.entries(files)) {
  byKey.set(path.replace('/src/assets/products/', ''), mod.default);
}

export function image(key: string): ImageMetadata | undefined {
  return byKey.get(key);
}

export type Img = {
  key: string; role: string; width: number; height: number;
  focusX?: number; focusY?: number; bg?: string;
};

/** CSS object-position that keeps the product in frame when a card crops. */
export function focus(img?: Img): string {
  const x = Math.round((img?.focusX ?? 0.5) * 100);
  const y = Math.round((img?.focusY ?? 0.5) * 100);
  return `${x}% ${y}%`;
}

export function pick(images: Img[], role: string): Img | undefined {
  return images.find((i) => i.role === role);
}

/** The best image to represent a product in a grid.
 *  Vector assets are wordmarks, so only real photography competes. Role wins
 *  first -- the hero is the shot Motorola chose -- and among equals the
 *  squarest image wins, because a letterbox banner crops badly in a card. */
export function cover(images: Img[], coverKey = ''): Img | undefined {
  const chosen = coverKey ? images.find((i) => i.key === coverKey) : undefined;
  if (chosen) return chosen;
  const photos = images.filter((i) => i.role !== 'logo' && i.width > 0 && i.height > 0);
  const order = ['hero', 'feature', 'gallery', 'spec'];
  for (const role of order) {
    const pool = photos.filter((i) => i.role === role);
    if (!pool.length) continue;
    return pool.sort((a, b) => a.width / a.height - b.width / b.height)[0];
  }
  return photos[0] ?? images[0];
}
