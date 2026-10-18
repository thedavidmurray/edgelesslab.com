const fs = require('fs');
const src = fs.readFileSync('src/lib/blog.ts', 'utf8');
const marker = 'export const posts';
const start = src.indexOf(marker);
console.log('start:', start);
if (start === -1) { console.log('marker not found'); process.exit(1); }
const section = src.slice(start);
console.log('section length:', section.length);
const slugRegex = /slug:\\s*\"([^\"]+)\"/g;
let match;
const slugs = [];
while ((match = slugRegex.exec(section)) !== null) {
  slugs.push(match[1]);
}
console.log('slugs:', slugs.length);
console.log('first 5:', slugs.slice(0,5));