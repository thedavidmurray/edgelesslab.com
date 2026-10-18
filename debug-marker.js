#!/usr/bin/env node
import { readFileSync } from "node:fs";

const ROOT = process.cwd();

function read(path) {
  return readFileSync(`${ROOT}/${path}`, "utf8");
}

const blogSrc = read("src/lib/blog.ts");
console.log('File length:', blogSrc.length);
const marker = `export const posts`;
const start = blogSrc.indexOf(marker);
console.log(`Marker "${marker}" found at index: ${start}`);
if (start !== -1) {
  console.log('Context:', blogSrc.slice(start-20, start+50));
}
const section = blogSrc.slice(start);
console.log('Section length:', section.length);
console.log('First 100 chars of section:', section.slice(0,100));
const slugRegex = /slug:\\s*\"([^\"]+)\"/g;
let match;
const slugs = [];
while ((match = slugRegex.exec(section)) !== null) {
  slugs.push(match[1]);
}
console.log('Slugs found:', slugs.length);
console.log('First 10 slugs:', slugs.slice(0,10));