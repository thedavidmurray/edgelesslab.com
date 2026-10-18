#!/usr/bin/env node
import { readFileSync } from "node:fs";

function read(path) {
  return readFileSync(`${process.cwd()}/${path}`, "utf8");
}

function getSlugsFromVariable(src, varName) {
  // Pattern: (export\s+)?const\s+varName\s*=\s*\[
  const pattern = new RegExp(`(?:export\\s+)?const\\s+${varName}\\s*=\\s*\\[`);
  const match = pattern.exec(src);
  if (!match) {
    console.log(`Variable ${varName} not found`);
    return [];
  }
  console.log(`Found ${varName} at index ${match.index}`);
  let start = match.index + match[0].length; // position after the '['
  console.log(`Start index: ${start}`);
  // Now find the matching closing bracket
  let depth = 1;
  let i = start;
  while (i < src.length && depth > 0) {
    const ch = src[i];
    if (ch === '[') depth++;
    else if (ch === ']') depth--;
    i++;
  }
  console.log(`End index: ${i}, depth after loop: ${depth}`);
  if (depth !== 0) {
    console.log(`Could not find matching bracket for ${varName}`);
    return [];
  }
  const arrayStr = src.slice(start, i-1); // exclude the closing ']'
  console.log(`Array string length: ${arrayStr.length}`);
  // Now find all slug: "..." in arrayStr
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let slugMatch;
  const slugs = [];
  while ((slugMatch = slugRegex.exec(arrayStr)) !== null) {
    slugs.push(slugMatch[1]);
  }
  console.log(`Found ${slugs.length} slugs`);
  return slugs;
}

const blogSrc = read("src/lib/blog.ts");
console.log("Testing blog.ts allPosts");
const slugs1 = getSlugsFromVariable(blogSrc, "allPosts");
console.log("Slugs:", slugs1.slice(0,5));

console.log("\nTesting blog-new-posts.ts newPosts");
const blogNewPostsSrc = read("src/lib/blog-new-posts.ts");
const slugs2 = getSlugsFromVariable(blogNewPostsSrc, "newPosts");
console.log("Slugs:", slugs2.slice(0,5));

console.log("\nTesting data.ts products");
const dataSrc = read("src/lib/data.ts");
const slugs3 = getSlugsFromVariable(dataSrc, "products");
console.log("Slugs:", slugs3.slice(0,5));