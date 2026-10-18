#!/usr/bin/env node
import { readFileSync } from "node:fs";

const ROOT = process.cwd();

function read(path) {
  return readFileSync(`${ROOT}/${path}`, "utf8");
}

function collectSlugs(src, exportName) {
  const marker = `export const ${exportName}`;
  const start = src.indexOf(marker);
  if (start === -1) return [];
  const section = src.slice(start);
  const slugRegex = /slug:\\s*\"([^\"]+)\"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(section)) !== null) {
    slugs.push(match[1]);
  }
  return slugs;
}

const blogSrc = read("src/lib/blog.ts");
const blogNewPostsSrc = read("src/lib/blog-new-posts.ts");
const dataSrc = read("src/lib/data.ts");

console.log("blog.ts posts slugs:", collectSlugs(blogSrc, "posts").length);
console.log("blog-new-posts.ts newPosts slugs:", collectSlugs(blogNewPostsSrc, "newPosts").length);
console.log("data.ts products slugs:", collectSlugs(dataSrc, "products").length);
console.log("data.ts projects slugs:", collectSlugs(dataSrc, "projects").length);
console.log("data.ts experiments slugs:", collectSlugs(dataSrc, "experiments").length);

// Let's also print first 5 of each
console.log("First 5 blog posts:", collectSlugs(blogSrc, "posts").slice(0,5));
console.log("First 5 blog newPosts:", collectSlugs(blogNewPostsSrc, "newPosts").slice(0,5));