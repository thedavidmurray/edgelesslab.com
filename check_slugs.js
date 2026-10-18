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
if (content) {
  const slugRegex = /slug:\s*"([^"]+)"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(content)) !== null) {
    slugs.push(match[1]);
  }
  console.log('Found slugs:', slugs.length);
  const target = [
    'youtube-mining-ai-agents',
    'self-healing-ai-infrastructure',
    'how-claude-code-memory-works',
    'the-hook-that-saved-my-codebase',
    '12-dollar-ai-operations-team',
    'agents-that-talk-to-each-other',
    'building-ai-agent-infrastructure-solo'
  ];
  console.log('\nChecking targets:');
  target.forEach(t => {
    console.log(`${t}: ${slugs.includes(t) ? 'FOUND' : 'MISSING'}`);
  });
}
