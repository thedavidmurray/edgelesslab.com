const fs = require('fs');
const src = fs.readFileSync('src/lib/blog.ts', 'utf8');
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
const content = getVariableArrayContent(src, 'allPosts');
console.log('Result:', content === null ? 'null' : `'${content}'`);
console.log('Length:', content === null ? 0 : content.length);
if (content !== null && content.length > 0) {
  console.log('First 50 chars:', content.slice(0,50));
  console.log('Last 50 chars:', content.slice(-50));
}
