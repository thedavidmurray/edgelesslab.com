import { readdirSync, readFileSync } from 'fs';
import { join } from 'path';

function walk(dir, results = []) {
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) walk(full, results);
    else if (e.name === 'page.tsx' || e.name === 'page.mdx') results.push(full);
  }
  return results;
}

const pages = walk('src/app');
let missingMeta = 0;
let missingAlt = 0;
const missingMetaPages = [];
const missingAltPages = [];

for (const p of pages) {
  const content = readFileSync(p, 'utf8');
  const hasMeta = content.includes('createPageMetadata') || content.includes('export const metadata') || content.includes('export async function generateMetadata');
  if (!hasMeta) {
    missingMeta++;
    missingMetaPages.push(p);
  }
  const imgMatches = content.match(/<(img|Image)[^>]*>/g);
  if (imgMatches) {
    for (const img of imgMatches) {
      if (!img.includes('alt=')) {
        missingAlt++;
        missingAltPages.push(`${p}: ${img.substring(0, 80)}`);
      }
    }
  }
}

console.log('=== SEO Audit Results ===');
console.log(`Total pages: ${pages.length}`);
console.log(`Pages with metadata: ${pages.length - missingMeta}`);
console.log(`Pages MISSING metadata: ${missingMeta}`);
if (missingMetaPages.length) {
  console.log('  Missing metadata:');
  missingMetaPages.forEach(p => console.log(`    - ${p}`));
}
console.log(`Images missing alt: ${missingAlt}`);
if (missingAltPages.length) {
  console.log('  Missing alt:');
  missingAltPages.forEach(p => console.log(`    - ${p}`));
}
console.log(`\nStatus: ${missingMeta === 0 && missingAlt === 0 ? 'PASS' : 'FAIL'}`);
process.exit(missingMeta === 0 && missingAlt === 0 ? 0 : 1);