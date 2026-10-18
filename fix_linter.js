const fs = require('fs');
const filePath = 'scripts/lint-blog-links.mjs';
let content = fs.readFileSync(filePath, 'utf8');
// Replace the getVariableArrayContent function
const newFunction = `function getVariableArrayContent(src, varName) {
  // Look for: const varName or export const varName
  let pos = src.indexOf(\`const \${varName}\`);
  if (pos === -1) {
    pos = src.indexOf(\`export const \${varName}\`);
  }
  if (pos === -1) {
    // console.log(\`Variable \${varName} not found\`);
    return null;
  }
  // Find the '=' after the variable declaration
  let equalsPos = src.indexOf('=', pos);
  if (equalsPos === -1) {
    // console.log(\`No '=' found for \${varName}\`);
    return null;
  }
  // Find the first '[' after the '='
  let bracketStart = src.indexOf('[', equalsPos);
  if (bracketStart === -1) {
    // console.log(\`No opening bracket found for \${varName}\`);
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
  // console.log(\`Could not find matching closing bracket for \${varName}\`);
  return null;
}`;
// Use regex to replace the function (assuming it's the only one)
const regex = /function getVariableArrayContent\(src, varName\) \{[\s\S]*?return null;\}/g;
const newContent = content.replace(regex, newFunction + '\n');
fs.writeFileSync(filePath, newContent);
console.log('Fixed linter script');
