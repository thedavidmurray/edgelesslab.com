#!/usr/bin/env node
import { readFileSync } from "node:fs";

const src = readFileSync("src/lib/blog.ts", "utf8");
console.log("First 50 chars:", src.slice(0,50));
console.log("Line 7:", src.split('\n')[6]); // 0-indexed
const pos1 = src.indexOf("const allPosts");
console.log("Index of 'const allPosts':", pos1);
if (pos1 !== -1) {
  console.log("Context:", src.slice(pos1-10, pos1+30));
}
const pos2 = src.indexOf("export const allPosts");
console.log("Index of 'export const allPosts':", pos2);