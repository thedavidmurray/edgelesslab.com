const fs = require('fs');
const src = fs.readFileSync('src/lib/blog.ts', 'utf8');
// Find the start of allPosts array
const startMatch = src.match(/const allPosts: BlogPost\[\] = \[/);
if (!startMatch) {
  console.log('Start not found');
  process.exit(1);
}
const startIndex = startMatch.index + startMatch[0].length; // position after the opening '['
let depth = 1;
let i = startIndex;
while (i < src.length) {
  const ch = src[i];
  if (ch === '[') depth++;
  else if (ch === ']') depth--;
  if (depth === 0) {
    console.log('Matching closing bracket at index:', i);
    console.log('Line number approx:', src.slice(0, i).split('\n').length);
    // Show context
    const before = src.slice(Math.max(0, i - 20), i);
    const after = src.slice(i, Math.min(src.length, i + 20));
    console.log('Context:', before + '[' + after + ']'); // Actually we have the bracket at i
    break;
  }
  i++;
}
if (depth !== 0) {
  console.log('No matching closing bracket found');
}
