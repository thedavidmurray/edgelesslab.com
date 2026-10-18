const fs = require('fs');
const src = fs.readFileSync('src/lib/blog.ts', 'utf8');
function getVariableArrayContent(src, varName) {
  let pos = src.indexOf(`const ${varName}`);
  if (pos === -1) {
    pos = src.indexOf(`export const ${varName}`);
  }
  if (pos === -1) {
    return null;
  }
  let bracketStart = src.indexOf('[', pos);
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
const content = getVariableArrayContent(src, 'allPosts');
console.log('Content length:', content ? content.length : 0);
if (content) {
  // Show first 200 and last 200 chars
  console.log('First 200:', content.slice(0,200));
  console.log('Last 200:', content.slice(-200));
  // Check for slugs
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(content)) !== null) {
    slugs.push(match[1]);
  }
  console.log('Slugs found:', slugs.length);
  console.log('Slugs:', slugs);
}
