const fs = require('fs');
const src = fs.readFileSync('src/lib/blog.ts', 'utf8');
function getVariableArrayContent(src, varName) {
  console.log('Looking for:', varName);
  let pos = src.indexOf(`const ${varName}`);
  console.log('pos const:', pos);
  if (pos === -1) {
    pos = src.indexOf(`export const ${varName}`);
    console.log('pos export const:', pos);
  }
  if (pos === -1) {
    console.log('Variable not found');
    return null;
  }
  // Find the '=' after the variable declaration
  let equalsPos = src.indexOf('=', pos);
  console.log('equalsPos:', equalsPos);
  if (equalsPos === -1) {
    console.log(\`No '=' found for \${varName}\`);
    return null;
  }
  // Find the first '[' after the '='
  let bracketStart = src.indexOf('[', equalsPos);
  console.log('bracketStart:', bracketStart);
  if (bracketStart === -1) {
    console.log(\`No opening bracket found for \${varName}\`);
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
      console.log('Found matching closing bracket at:', i);
      return src.slice(bracketStart + 1, i); // exclude the brackets
    }
    i++;
  }
  console.log('Could not find matching closing bracket');
  return null;
}
const content = getVariableArrayContent(src, 'allPosts');
console.log('content length:', content ? content.length : 0);
if (content) {
  console.log('First 200 chars:', content.slice(0,200));
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(content)) !== null) {
    slugs.push(match[1]);
  }
  console.log('Slugs found:', slugs);
}
