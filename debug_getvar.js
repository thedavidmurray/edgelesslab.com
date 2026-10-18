const fs = require('fs');
function getVariableArrayContent(src, varName) {
  // Look for: const varName or export const varName
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
const blogSrc = fs.readFileSync('src/lib/blog.ts', 'utf8');
const newPostsSrc = fs.readFileSync('src/lib/blog-new-posts.ts', 'utf8');
console.log('blog.ts allPosts:');
let blogContent = getVariableArrayContent(blogSrc, 'allPosts');
if (blogContent === null) {
  console.log('  null');
} else {
  console.log('  length:', blogContent.length);
  console.log('  first 100 chars:', blogContent.slice(0,100));
  console.log('  last 100 chars:', blogContent.slice(-100));
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(blogContent)) !== null) {
    slugs.push(match[1]);
  }
  console.log('  slugs found:', slugs.length);
}
console.log('blog-new-posts.ts newPosts:');
let newPostsContent = getVariableArrayContent(newPostsSrc, 'newPosts');
if (newPostsContent === null) {
  console.log('  null');
} else {
  console.log('  length:', newPostsContent.length);
  console.log('  first 100 chars:', newPostsContent.slice(0,100));
  console.log('  last 100 chars:', newPostsContent.slice(-100));
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(newPostsContent)) !== null) {
    slugs.push(match[1]);
  }
  console.log('  slugs found:', slugs.length);
}
