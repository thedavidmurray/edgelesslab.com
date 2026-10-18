#!/usr/bin/env node
import { readFileSync } from "node:fs";

function read(path) {
  return readFileSync(`${process.cwd()}/${path}`, "utf8");
}

function getSlugsFromVariable(src, varName) {
  // Pattern: (export\s+)?const\s+varName\s*=\s*\[
  const pattern = new RegExp(`(export\\s+)?const\\s+${varName}\\s*=\\s*\\[`);
  const match = pattern.exec(src);
  if (!match) {
    console.log(`Variable ${varName} not found`);
    return [];
  }
  let start = match.index + match[0].length; // position after the '['
  // Now find the matching closing bracket
  let depth = 1;
  let i = start;
  while (i < src.length && depth > 0) {
    const ch = src[i];
    if (ch === '[') depth++;
    else if (ch === ']') depth--;
    i++;
  }
  if (depth !== 0) {
    console.log(`Could not find matching bracket for ${varName}`);
    return [];
  }
  const arrayStr = src.slice(start, i-1); // exclude the closing ']'
  // Now find all slug: "..." in arrayStr
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let slugMatch;
  const slugs = [];
  while ((slugMatch = slugRegex.exec(arrayStr)) !== null) {
    slugs.push(slugMatch[1]);
  }
  return slugs;
}

const blogSrc = read("src/lib/blog.ts");
const blogNewPostsSrc = read("src/lib/blog-new-posts.ts");
const dataSrc = read("src/lib/data.ts");

console.log("blog.ts allPosts slugs:", getSlugsFromVariable(blogSrc, "allPosts").length);
console.log("blog-new-posts.ts newPosts slugs:", getSlugsFromVariable(blogNewPostsSrc, "newPosts").length);
console.log("data.ts products slugs:", getSlugsFromVariable(dataSrc, "products").length);
console.log("data.ts projects slugs:", getSlugsFromVariable(dataSrc, "projects").length);
console.log("data.ts experiments slugs:", getSlugsFromVariable(dataSrc, "experiments").length);

// Show first few
console.log("First 5 blog.ts allPosts:", getSlugsFromVariable(blogSrc, "allPosts").slice(0,5));
console.log("First 5 blog-new-posts.ts newPosts:", getSlugsFromVariable(blogNewPostsSrc, "newPosts").slice(0,5));