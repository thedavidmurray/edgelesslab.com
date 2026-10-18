const fs = require('fs');
function getVariableArrayContent(src, varName) {
  let pos = src.indexOf('const ' + varName);
  if (pos === -1) {
    pos = src.indexOf('export const ' + varName);
  }
  if (pos === -1) {
    return null;
  }
  let equalsPos = src.indexOf('=', pos);
  if (equalsPos === -1) {
    return null;
  }
  let bracketStart = src.indexOf('[', equalsPos);
  if (bracketStart === -1) {
    return null;
  }
  let depth = 0;
  let i = bracketStart;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '[') depth++;
    else if (ch === ']') depth--;
    if (depth === 0) {
      return src.slice(bracketStart + 1, i);
    }
    i++;
  }
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
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(newPostsContent)) !== null) {
    slugs.push(match[1]);
  }
  console.log('  slugs found:', slugs.length);
}
