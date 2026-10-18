#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

function read(path) {
  return readFileSync(resolve(ROOT, path), "utf8");
}

function collectSlugs(src, exportName) {
  const marker = `export const ${exportName}`;
  const start = src.indexOf(marker);
  console.log(`Looking for ${exportName}: marker index = ${start}`);
  if (start === -1) {
    console.log(`Marker not found for ${exportName}`);
    return [];
  }
  const section = src.slice(start);
  console.log(`Section length for ${exportName}: ${section.length}`);
  const slugRegex = /slug:\\s*\"([^\"]+)\"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(section)) !== null) {
    slugs.push(match[1]);
  }
  console.log(`Found ${slugs.length} slugs for ${exportName}:`, slugs.slice(0, 5));
  return slugs;
}

const blogSrc = read("src/lib/blog.ts");
const blogNewPostsSrc = read("src/lib/blog-new-posts.ts");
const dataSrc = read("src/lib/data.ts");

console.log("=== blog.ts posts ===");
collectSlugs(blogSrc, "posts");
console.log("=== blog-new-posts.ts newPosts ===");
collectSlugs(blogNewPostsSrc, "newPosts");
console.log("=== data.ts products ===");
collectSlugs(dataSrc, "products");
console.log("=== data.ts projects ===");
collectSlugs(dataSrc, "projects");
console.log("=== data.ts experiments ===");
collectSlugs(dataSrc, "experiments");