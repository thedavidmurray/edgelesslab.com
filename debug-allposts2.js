#!/usr/bin/env node
import { readFileSync } from "node:fs";

const src = readFileSync("src/lib/blog.ts", "utf8");
const lines = src.split('\n');
console.log("Line 7:", lines[6]); // 0-indexed
console.log("Line 8:", lines[7]);
console.log("Line 9:", lines[8]);

const pos = src.indexOf("const allPosts");
console.log("Index of 'const allPosts':", pos);
if (pos !== -1) {
  console.log("Context:", src.slice(pos, pos+50));
}

// Look for '[' after that pos
const bracketStart = src.indexOf('[', pos);
console.log("Index of '[' after const allPosts:", bracketStart);
if (bracketStart !== -1) {
  console.log("Context around bracket:", src.slice(bracketStart-10, bracketStart+10));
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
    break;
  }
  i++;
}
if (i === src.length) {
  console.log("Did not find matching closing bracket");
} else {
  const arrayStr = src.slice(bracketStart+1, i);
  console.log("Array string length:", arrayStr.length);
  console.log("First 200 chars of array:", arrayStr.slice(0,200));
}