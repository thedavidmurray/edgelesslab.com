#!/usr/bin/env node
import { readFileSync } from "node:fs";

const ROOT = process.cwd();

function read(path) {
  return readFileSync(`${ROOT}/${path}`, "utf8");
}

function collectSlugsGlobal(src) {
  const slugRegex = /slug:\\s*\"([^\"]+)\"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(src)) !== null) {
    slugs.push(match[1]);
  }
  return slugs;
}

const blogSrc = read("src/lib/blog.ts");
console.log('blog.ts total length:', blogSrc.length);
const slugs = collectSlugsGlobal(blogSrc);
console.log('blog.ts slugs count:', slugs.length);
console.log('First 10:', slugs.slice(0,10));

// Also check for duplicates
const set = new Set(slugs);
console.log('Unique slugs:', set.size);
if (set.size !== slugs.length) {
  console.log('Duplicates:', slugs.filter((s, i) => slugs.indexOf(s) !== i));
}