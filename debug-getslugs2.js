#!/usr/bin/env node
import { readFileSync } from "node:fs";

function read(path) {
  return readFileSync(`${process.cwd()}/${path}`, "utf8");
}

function getVariableArrayContent(src, varName) {
  let pos = src.indexOf(`const ${varName}`);
  if (pos === -1) {
    pos = src.indexOf(`export const ${varName}`);
  }
  if (pos === -1) {
    // console.log(`Variable ${varName} not found`);
    return null;
  }
  // Find the first '[' after the variable declaration
  let bracketStart = src.indexOf('[', pos);
  if (bracketStart === -1) {
    // console.log(`No opening bracket found for ${varName}`);
    return null;
  }
  // Now find the matching closing bracket
  let depth = 0;
  let i = bracketStart;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '[') depth++;
    else if (ch === ']') depth--;
    if (depth === 0) {
      // Found matching closing bracket
      return src.slice(bracketStart + 1, i); // exclude the brackets
    }
    i++;
  }
  // console.log(`Could not find matching closing bracket for ${varName}`);
  return null;
}

function getSlugsFromVariableArray(arrayContent) {
  if (arrayContent === null) return [];
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(arrayContent)) !== null) {
    slugs.push(match[1]);
  }
  return slugs;
}

const blogSrc = read("src/lib/blog.ts");
console.log("Testing blog.ts allPosts");
const blogArray = getVariableArrayContent(blogSrc, "allPosts");
console.log("Array content length:", blogArray ? blogArray.length : "null");
const slugs1 = getSlugsFromVariableArray(blogArray);
console.log("Slugs count:", slugs1.length);
console.log("First 5:", slugs1.slice(0,5));

console.log("\nTesting blog-new-posts.ts newPosts");
const blogNewPostsSrc = read("src/lib/blog-new-posts.ts");
const blogNewPostsArray = getVariableArrayContent(blogNewPostsSrc, "newPosts");
console.log("Array content length:", blogNewPostsArray ? blogNewPostsArray.length : "null");
const slugs2 = getSlugsFromVariableArray(blogNewPostsArray);
console.log("Slugs count:", slugs2.length);
console.log("First 5:", slugs2.slice(0,5));

console.log("\nTesting data.ts products");
const dataSrc = read("src/lib/data.ts");
const productsArray = getVariableArrayContent(dataSrc, "products");
console.log("Array content length:", productsArray ? productsArray.length : "null");
const slugs3 = getSlugsFromVariableArray(productsArray);
console.log("Slugs count:", slugs3.length);
console.log("First 5:", slugs3.slice(0,5));

console.log("\nTesting data.ts projects");
const projectsArray = getVariableArrayContent(dataSrc, "projects");
console.log("Array content length:", projectsArray ? projectsArray.length : "null");
const slugs4 = getSlugsFromVariableArray(projectsArray);
console.log("Slugs count:", slugs4.length);
console.log("First 5:", slugs4.slice(0,5));

console.log("\nTesting data.ts experiments");
const experimentsArray = getVariableArrayContent(dataSrc, "experiments");
console.log("Array content length:", experimentsArray ? experimentsArray.length : "null");
const slugs5 = getSlugsFromVariableArray(experimentsArray);
console.log("Slugs count:", slugs5.length);
console.log("First 5:", slugs5.slice(0,5));