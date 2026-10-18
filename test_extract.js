const fs = require('fs');
const src = fs.readFileSync('src/lib/blog.ts', 'utf8');
// Find the position of "const allPosts: BlogPost[] = ["
const match = src.match(/const allPosts: BlogPost\[\] = \[/);
if (!match) {
  console.log('Pattern not found');
  process.exit(1);
}
const startIndex = match.index + match[0].length; // after the '['
let depth = 1;
let i = startIndex;
while (i < src.length) {
  const ch = src[i];
  if (ch === '[') depth++;
  else if (ch === ']') depth--;
  if (depth === 0) {
    console.log('Matching closing bracket at index:', i);
    const content = src.slice(startIndex, i);
    console.log('Content length:', content.length);
    console.log('First 200 chars:', content.slice(0,200));
    console.log('Last 200 chars:', content.slice(-200));
    break;
  }
  i++;
}
