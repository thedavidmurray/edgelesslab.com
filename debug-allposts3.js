#!/usr/bin/env node
import { readFileSync } from "node:fs";

const src = readFileSync("src/lib/blog.ts", "utf8");
console.log("File length:", src.length);

const lines = src.split('\n');
for (let i = 6; i < 10; i++) {
  console.log(`${i+1}: ${lines[i]}`);
}

// Find the exact substring
const pos = src.indexOf("const allPosts");
console.log("\nIndex of 'const allPosts':", pos);
if (pos !== -1) {
  console.log("Matched substring:", src.slice(pos, pos+30));
}

// Now look for '[' after pos
let bracketStart = -1;
for (let i = pos; i < src.length; i++) {
  if (src[i] === '[') {
    bracketStart = i;
    break;
  }
}
console.log("Index of '[' after const allPosts:", bracketStart);
if (bracketStart !== -1) {
  console.log("Char before bracket:", src[bracketStart-1]);
  console.log("Context:", src.slice(bracketStart-5, bracketStart+5));
}

// Now find matching closing bracket
let depth = 0;
let i = bracketStart;
while (i < src.length) {
  const ch = src[i];
  if (ch === '[') depth++;
  else if (ch === ']') depth--;
  if (depth === 0 && i > bracketStart) {
    console.log("Matching closing bracket at index:", i);
    console.log("Content between brackets length:", i - bracketStart - 1);
    break;
  }
  i++;
}
if (i === src.length) {
  console.log("Did not find matching closing bracket");
} else {
  const arrayStr = src.slice(bracketStart+1, i);
  console.log("Array string first 100 chars:", arrayStr.slice(0,100));
  console.log("Array string last 100 chars:", arrayStr.slice(-100));
  // Now try to find slugs
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(arrayStr)) !== null) {
    slugs.push(match[1]);
  }
  console.log("Slugs found:", slugs.length);
  console.log("First 5 slugs:", slugs.slice(0,5));
}