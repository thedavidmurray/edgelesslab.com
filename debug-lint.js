#!/usr/bin/env node
const { readFileSync, readdirSync, existsSync, statSync } = require("node:fs");
const { dirname, resolve, join } = require("node:path");
const { fileURLToPath } = require("node:url");

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

const files = ["src/lib/blog.ts", "src/lib/blog-new-posts.ts", "src/lib/data.ts"];

function read(path) {
  return readFileSync(resolve(ROOT, path), "utf8");
}

function collectSlugs(src, exportName) {
  const marker = `export const ${exportName}`;
  const start = src.indexOf(marker);
  if (start === -1) return [];
  const section = src.slice(start);
  const slugRegex = /slug:\\s*\"([^\"]+)\"/g;
  let match;
  const slugs = [];
  while ((match = slugRegex.exec(section)) !== null) {
    slugs.push(match[1]);
  }
  return slugs;
}

function isAppRouteDir(name) {
  if (name.startsWith(".")) return false;
  if (name.startsWith("_")) return false;
  if (name.endsWith(".tsx") || name.endsWith(".ts") || name.endsWith(".css") || name.endsWith(".ico") || name.endsWith(".bak")) {
    return false;
  }
  return true;
}

function discoverAppRoutes() {
  const appDir = resolve(ROOT, "src/app");
  const routes = new Set(["/"]);
  if (!existsSync(appDir)) return routes;
  for (const entry of readdirSync(appDir)) {
    if (!isAppRouteDir(entry)) continue;
    const full = join(appDir, entry);
    const st = statSync(full);
    if (!st.isDirectory()) continue;
    const hasPage = existsSync(resolve(full, "page.tsx"));
    if (hasPage) {
      routes.add(`/${entry}`);
    }
  }
  return routes;
}

function discoverPublicRoutes() {
  const publicDir = resolve(ROOT, "public");
  const routes = new Set();
  if (!existsSync(publicDir)) return routes;
  for (const entry of readdirSync(publicDir)) {
    if (entry.startsWith(".")) continue;
    const full = join(publicDir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      routes.add(`/${entry}`);
      for (const sub of readdirSync(full)) {
        if (sub.startsWith(".")) continue;
        const subFull = join(full, sub);
        let subPath = `/${entry}/${sub}`;
        const dotIdx = sub.lastIndexOf(".");
        if (dotIdx > 0) subPath = subPath.slice(0, dotIdx);
        routes.add(subPath);
      }
    } else {
      let p = `/${entry}`;
      const dotIdx = entry.lastIndexOf(".");
      if (dotIdx > 0) p = p.slice(0, dotIdx);
      else p = p.replace(/\\/$/, "");
      routes.add(p);
    }
  }
  return routes;
}

function addKnownRoutes() {
  const blogSrc = read("src/lib/blog.ts");
  const blogNewPostsSrc = read("src/lib/blog-new-posts.ts");
  const dataSrc = read("src/lib/data.ts");

  for (const route of discoverAppRoutes()) {
    appRoutes.add(route);
  }
  for (const route of discoverPublicRoutes()) {
    appRoutes.add(route);
  }

  for (const slug of collectSlugs(blogSrc, "posts")) {
    appRoutes.add(`/blog/${slug}`);
  }
  for (const slug of collectSlugs(blogNewPostsSrc, "newPosts")) {
    appRoutes.add(`/blog/${slug}`);
  }
  for (const slug of collectSlugs(dataSrc, "products")) {
    appRoutes.add(`/products/${slug}`);
  }
  for (const slug of collectSlugs(dataSrc, "projects")) {
    appRoutes.add(`/projects/${slug}`);
  }
  for (const slug of collectSlugs(dataSrc, "experiments")) {
    appRoutes.add(`/lab/${slug}`);
  }

  appRoutes.add("/blog/soul-memo");
  appRoutes.add("/blog/soul-memo/mark-cuban-effort");

  appRoutes.add("/services/private-ai-systems");
}

const appRoutes = new Set();
addKnownRoutes();

console.log("=== Collected slugs from blog.ts ===");
console.log(collectSlugs(read("src/lib/blog.ts"), "posts"));
console.log("=== Collected slugs from blog-new-posts.ts ===");
console.log(collectSlugs(read("src/lib/blog-new-posts.ts"), "newPosts"));
console.log("=== Number of appRoutes ===");
console.log(appRoutes.size);
console.log("=== First 20 appRoutes ===");
console.log([...appRoutes].slice(0, 20));

// Check specific routes
const targetSlugs = [
  "youtube-mining-ai-agents",
  "self-healing-ai-infrastructure",
  "how-claude-code-memory-works",
  "the-hook-that-saved-my-codebase",
  "12-dollar-ai-operations-team",
  "agents-that-talk-to-each-other",
  "building-ai-agent-infrastructure-solo"
];
console.log("=== Checking target slugs ===");
for (const slug of targetSlugs) {
  const route = `/blog/${slug}`;
  console.log(`${route}: ${appRoutes.has(route)}`);
}