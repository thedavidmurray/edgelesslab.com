import sys
import re

file_path = 'scripts/lint-blog-links.mjs'
with open(file_path, 'r') as f:
    content = f.read()

# Define the new function
new_func = '''function getVariableArrayContent(src, varName) {
  // Look for: const varName or export const varName
  let pos = src.indexOf(`const ${varName}`);
  if (pos === -1) {
    pos = src.indexOf(`export const ${varName}`);
  }
  if (pos === -1) {
    // console.log(`Variable ${varName} not found`);
    return null;
  }
  // Find the '=' after the variable declaration (skip type annotations)
  let equalsPos = src.indexOf('=', pos);
  if (equalsPos === -1) {
    // console.log(`No '=' found for ${varName}`);
    return null;
  }
  // Find the first '[' after the '='
  let bracketStart = src.indexOf('[', equalsPos);
  if (bracketStart === -1) {
    // console.log(`No opening bracket found for ${varName}`);
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
  // console.log(`Could not find matching closing bracket for ${varName}`);
  return null;
}'''

# Replace the old function with the new one
# We'll use a regex that matches from the start of the function to the start of the next function
pattern = r'function getVariableArrayContent\(src, varName\) \{[\s\S]*?function getSlugsFromVariableArray'
# We want to replace up to but not including the next function
# Let's do a more precise replacement: find the function and replace until the line before the next function
# We'll split by lines and reconstruct
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    if lines[i].strip().startswith('function getVariableArrayContent(src, varName) {'):
        # Skip the old function lines until we see the next function
        new_lines.append(new_func)
        # Advance i until we see the line that starts with 'function getSlugsFromVariableArray'
        while i < len(lines) and not lines[i].strip().startswith('function getSlugsFromVariableArray'):
            i += 1
        # Now we are at the line of the next function, we will add it in the next iteration
        continue
    else:
        new_lines.append(lines[i])
        i += 1

new_content = '\n'.join(new_lines)
with open(file_path, 'w') as f:
    f.write(new_content)
print('Fixed linter script')
