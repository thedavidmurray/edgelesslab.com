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
console.log('Array content length:', content ? content.length : 0);
if (content) {
  console.log('First 500 chars:');
  console.log(content.slice(0,500));
  console.log('---');
  console.log('Last 500 chars:');
  console.log(content.slice(-500));
}
