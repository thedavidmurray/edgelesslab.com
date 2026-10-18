1:"$Sreact.fragment"
2:I[56850,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],"Nav"]
3:I[65303,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],"BlogArticle"]
4:T12dd,<p>Every Claude Code session starts the same way: a blank slate. No memory of yesterday's architecture decisions. No recall of your coding conventions. No idea that you spent three hours debugging that OAuth flow last week.</p>
<p>This is the single biggest friction point in AI-assisted development. Not model capability. Not context windows. Memory.</p>
<h2 id="the-problem-is-structural">The Problem Is Structural</h2>
<p>Claude Code reads instructions from a file called <code>CLAUDE.md</code> at the start of every session. That's it. There's no built-in persistence layer. No session history. No learning from past interactions.</p>
<p>So every session, you repeat yourself: "We use TypeScript, not JavaScript." "The API lives in <code>src/api/</code>, not <code>api/</code>." "Don't use default exports." "We already tried approach X and it failed because Y."</p>
<p>This isn't a minor annoyance. It's a compounding tax on every interaction.</p>
<h2 id="file-based-memory-fixes-this">File-Based Memory Fixes This</h2>
<p>The solution is surprisingly simple: structured markdown files that Claude reads automatically at session start.</p>
<p>No databases. No vector stores. No infrastructure. Just files in your repo that Claude already knows how to read.</p>
<p>The memory system layers on top of Claude Code's built-in <code>CLAUDE.md</code> hierarchy. Claude loads these files automatically. You don't need plugins or configuration.</p>
<h2 id="the-4-memory-types">The 4 Memory Types</h2>
<p>After running this pattern in production across multiple projects, I've found four distinct memory types that cover every use case.</p>
<h3>1. User Memory</h3>
<p>Who you are and how you work. Follows you across every project.</p>
<pre><code>name: User Role
type: user
---
Senior backend engineer, 8 years Go.
New to React frontend in this project.
Prefer explanations mapping frontend concepts to backend analogues.</code></pre>
<h3>2. Feedback Memory</h3>
<p>Corrections that stick. The highest-value memory type. Every correction makes every future session better.</p>
<pre><code>name: No mocking in integration tests
type: feedback
---
Integration tests must hit a real database, not mocks.
Why: Mocked tests passed but prod migration failed last quarter.</code></pre>
<h3>3. Project Memory</h3>
<p>Architecture decisions, conventions, and infrastructure specific to one codebase.</p>
<pre><code>name: API Migration Freeze
type: project
---
No breaking API changes until 2026-03-15 (mobile release cut).
Any endpoint modifications must be backwards-compatible.</code></pre>
<h3>4. Reference Memory</h3>
<p>Pointers to where things live. Tools, APIs, dashboards.</p>
<pre><code>name: Bug Tracker
type: reference
---
Production bugs: Linear project "PLATFORM"
Feature requests: Linear project "ROADMAP"
Design specs: Figma workspace "Product Design 2026"</code></pre>
<h2 id="what-changes-in-practice">What Changes in Practice</h2>
<p>With memory in place, sessions start differently. Instead of 10 minutes of context-setting, you jump straight into the work.</p>
<p>Claude remembers that your test suite uses Vitest, not Jest. It knows the deploy script is at <code>scripts/deploy.sh</code>, not <code>deploy.sh</code>. It recalls that you tried Redis caching last month and hit connection pooling issues.</p>
<p>After a month of accumulated feedback memory, Claude makes roughly 60% fewer mistakes that require correction. That's not a benchmark; that's from tracking corrections across my own projects.</p>
<h2 id="the-maintenance-problem">The Maintenance Problem</h2>
<p>Raw memory files work, but they accumulate cruft. Outdated entries. Contradictory instructions. Files that grow past useful size.</p>
<p>The discipline: review monthly, archive aggressively, keep each file under 200 lines. Memory that's too long defeats the purpose; Claude spends context window on stale instructions instead of your actual task.</p>
<h2 id="get-started">Get Started</h2>
<p>I've open-sourced the base memory kit with templates for all four memory types, a starter CLAUDE.md structure, and setup instructions.</p>
<p><strong>Free:</strong> <a href="https://github.com/edgeless-ai/claude-memory-kit">Claude Memory Kit on GitHub</a></p>
<p>The free version covers 90% of use cases. For production patterns including stack-specific libraries (React/Next.js, Python/FastAPI, Go, Rails, Rust), multi-project memory architectures, and CLAUDE.md templates:</p>
<p><strong>Update — free resources:</strong> The Pro download is retired. <a href="https://edgelessai.gumroad.com/l/edgeless-free-kit?wanted=true&price=0">Get the Edgeless Free Kit</a> for the available references and templates; the former Pro file is not included.</p>
<p>The best time to set up memory is before your next session. Takes 15 minutes, saves hours every week.</p>b:X
10:X
10:C
0:{"buildId":"ILG6gReoatO94noDnyNVS","data":[{"rsc":["$","$1","c",{"children":[["$","div",null,{"className":"flex flex-col min-h-full","style":{"background":"var(--bg-base)"},"children":[["$","$L2",null,{}],["$","script",null,{"type":"application/ld+json","dangerouslySetInnerHTML":{"__html":"{\"@context\":\"https://schema.org\",\"@type\":\"BlogPosting\",\"headline\":\"How Claude Code Memory Actually Works\",\"description\":\"Claude forgets everything between sessions. File-based memory fixes that. The simplest setup, and why it changes how you work with AI.\",\"datePublished\":\"2026-03-21\",\"dateModified\":\"2026-03-21\",\"wordCount\":1500,\"author\":{\"@type\":\"Person\",\"name\":\"David Murray\",\"url\":\"https://edgelesslab.com/about\"},\"publisher\":{\"@type\":\"Organization\",\"name\":\"Edgeless Lab\",\"url\":\"https://edgelesslab.com\"},\"url\":\"https://edgelesslab.com/blog/how-claude-code-memory-works\",\"keywords\":[\"Claude Code\",\"Memory\",\"Developer Tools\"],\"mainEntityOfPage\":{\"@type\":\"WebPage\",\"@id\":\"https://edgelesslab.com/blog/how-claude-code-memory-works\"}}"}}],["$","script",null,{"type":"application/ld+json","dangerouslySetInnerHTML":{"__html":"{\"@context\":\"https://schema.org\",\"@type\":\"BreadcrumbList\",\"itemListElement\":[{\"@type\":\"ListItem\",\"position\":1,\"name\":\"Home\",\"item\":\"https://edgelesslab.com\"},{\"@type\":\"ListItem\",\"position\":2,\"name\":\"Blog\",\"item\":\"https://edgelesslab.com/blog\"},{\"@type\":\"ListItem\",\"position\":3,\"name\":\"How Claude Code Memory Actually Works\",\"item\":\"https://edgelesslab.com/blog/how-claude-code-memory-works\"}]}"}}],["$","article",null,{"className":"pt-28 pb-20 px-6","children":["$","div",null,{"className":"max-w-[960px] mx-auto","children":[["$","div",null,{"className":"mb-12 max-w-[680px]","children":["$undefined",["$","div",null,{"className":"flex items-center gap-3 mb-4","children":[["$","time",null,{"className":"text-xs font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-03-21","children":"March 21, 2026"}],["$","span",null,{"className":"text-xs font-mono","style":{"color":"var(--text-tertiary)"},"children":"6 min"}]]}],["$","h1",null,{"className":"text-3xl sm:text-4xl font-bold tracking-tight leading-[1.2] mb-4","style":{"color":"var(--text-primary)"},"children":"How Claude Code Memory Actually Works"}],["$","p",null,{"className":"text-lg font-light","style":{"color":"var(--text-secondary)","lineHeight":1.7},"children":"Claude forgets everything between sessions. File-based memory fixes that. The simplest setup, and why it changes how you work with AI."}],["$","div",null,{"className":"flex flex-wrap gap-2 mt-4","children":[["$","span","Claude Code",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"Claude Code"}],["$","span","Memory",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"Memory"}],["$","span","Developer Tools",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"Developer Tools"}]]}],"$undefined"]}],["$","$L3",null,{"html":"$4","editorial":true,"sidebar":null}],false,"$L5",false,false,"$L6"]}]}],"$L7"]}],["$L8"],"$L9"]}],"isPartial":"$@a","staleTime":"$b","varyParams":null},{"rsc":"$Lc","isPartial":"$@d","staleTime":"$b","varyParams":null},{"rsc":"$Le","isPartial":"$@f","staleTime":"$b","varyParams":"$10"},{"rsc":"$L11","isPartial":"$@12","staleTime":"$b","varyParams":"$10"}],"isUpgradeableISRFallback":false,"a":"$@13","rootVaryParams":null,"needsRuntimeRequest":"$@14"}
15:I[15715,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],""]
16:I[35822,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],"Footer"]
17:I[1913,["/_next/static/chunks/2cue0t2y-yu_9.js"],"OutletBoundary"]
18:"$Sreact.suspense"
1a:I[1913,["/_next/static/chunks/2cue0t2y-yu_9.js"],"ViewportBoundary"]
1b:I[1913,["/_next/static/chunks/2cue0t2y-yu_9.js"],"MetadataBoundary"]
1c:I[50529,["/_next/static/chunks/2cue0t2y-yu_9.js"],"IconMark"]
1d:I[67593,["/_next/static/chunks/2cue0t2y-yu_9.js"],"default"]
1e:I[92370,["/_next/static/chunks/2cue0t2y-yu_9.js"],"default"]
5:["$","section",null,{"className":"mt-16 pt-8 border-t","style":{"borderColor":"var(--border-subtle)"},"aria-label":"Related posts","children":[["$","h2",null,{"className":"text-sm font-mono uppercase tracking-[0.1em] mb-6","style":{"color":"var(--text-tertiary)"},"children":"Related Posts"}],["$","div",null,{"className":"grid gap-4 sm:grid-cols-3","children":[["$","$L15","the-hook-that-saved-my-codebase",{"href":"/blog/the-hook-that-saved-my-codebase","className":"group block p-4 rounded-lg border transition-colors","style":{"background":"var(--bg-surface)","borderColor":"var(--border-subtle)"},"children":[["$","div",null,{"className":"text-sm font-semibold mb-1 transition-colors group-hover:text-white","style":{"color":"var(--text-primary)"},"children":"The Hook That Saved My Codebase"}],["$","div",null,{"className":"text-xs line-clamp-2","style":{"color":"var(--text-tertiary)","lineHeight":1.5},"children":"A single Claude Code hook prevented a cascading rm -rf from wiping source files. The damage-control pattern, and 3 hooks you can steal today."}],["$","div",null,{"className":"flex items-center gap-2 mt-3","children":[["$","time",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-04-03","children":"Apr 2026"}],["$","span",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"children":"5 min"}]]}]]}],["$","$L15","one-file-memory-system",{"href":"/blog/one-file-memory-system","className":"group block p-4 rounded-lg border transition-colors","style":{"background":"var(--bg-surface)","borderColor":"var(--border-subtle)"},"children":[["$","div",null,{"className":"text-sm font-semibold mb-1 transition-colors group-hover:text-white","style":{"color":"var(--text-primary)"},"children":"The One-File Memory System That Changed How I Use Claude"}],["$","div",null,{"className":"text-xs line-clamp-2","style":{"color":"var(--text-tertiary)","lineHeight":1.5},"children":"You shouldn't have to re-explain your stack every session. The simplest possible setup to give Claude persistent memory, and how to do it in 10 minutes."}],["$","div",null,{"className":"flex items-center gap-2 mt-3","children":[["$","time",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-03-26","children":"Mar 2026"}],["$","span",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"children":"4 min"}]]}]]}],["$","$L15","edgeless-memory-v1-passive-recall",{"href":"/blog/edgeless-memory-v1-passive-recall","className":"group block p-4 rounded-lg border transition-colors","style":{"background":"var(--bg-surface)","borderColor":"var(--border-subtle)"},"children":[["$","div",null,{"className":"text-sm font-semibold mb-1 transition-colors group-hover:text-white","style":{"color":"var(--text-primary)"},"children":"edgeless-memory v1.0: One Install, Three Tiers, Passive Recall"}],["$","div",null,{"className":"text-xs line-clamp-2","style":{"color":"var(--text-tertiary)","lineHeight":1.5},"children":"Agent-agnostic persistent memory that ships as one CLI. SQLite + ChromaDB + Obsidian vault, 700 memories graphed, agents that recall by meaning without an explicit search step."}],["$","div",null,{"className":"flex items-center gap-2 mt-3","children":[["$","time",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-06-21","children":"Jun 2026"}],["$","span",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"children":"7 min"}]]}]]}]]}]]}]
6:["$","div",null,{"className":"mt-12 pt-8 border-t","style":{"borderColor":"var(--border-subtle)"},"children":["$","$L15",null,{"href":"/blog","className":"text-sm font-medium transition-colors hover:text-white","style":{"color":"var(--text-secondary)"},"children":"← All posts"}]}]
7:["$","$L16",null,{}]
8:["$","script","script-0",{"src":"/_next/static/chunks/3x4v8a24_pq_9.js","async":true}]
9:["$","$L17",null,{"children":["$","$18",null,{"name":"Next.MetadataOutlet","children":"$@19"}]}]
c:["$","$1","h",{"children":[null,["$","$L1a",null,{"children":[["$","meta","0",{"charSet":"utf-8"}],["$","meta","1",{"name":"viewport","content":"width=device-width, initial-scale=1"}]]}],["$","div",null,{"hidden":true,"children":["$","$L1b",null,{"children":["$","$18",null,{"name":"Next.Metadata","children":[["$","title","0",{"children":"How Claude Code Memory Actually Works | Edgeless Lab"}],["$","meta","1",{"name":"description","content":"Claude forgets everything between sessions. File-based memory fixes that. The simplest setup, and why it changes how you work with AI."}],["$","meta","2",{"name":"keywords","content":"Claude Code,Memory,Developer Tools"}],["$","meta","3",{"name":"robots","content":"index, follow"}],["$","meta","4",{"name":"googlebot","content":"index, follow"}],["$","link","5",{"rel":"canonical","href":"https://edgelesslab.com/blog/how-claude-code-memory-works/"}],["$","meta","6",{"property":"og:title","content":"How Claude Code Memory Actually Works | Edgeless Lab"}],["$","meta","7",{"property":"og:description","content":"Claude forgets everything between sessions. File-based memory fixes that. The simplest setup, and why it changes how you work with AI."}],["$","meta","8",{"property":"og:url","content":"https://edgelesslab.com/blog/how-claude-code-memory-works/"}],["$","meta","9",{"property":"og:site_name","content":"Edgeless Lab"}],["$","meta","10",{"property":"og:image","content":"https://edgelesslab.com/og-image.webp"}],["$","meta","11",{"property":"og:image:width","content":"1200"}],["$","meta","12",{"property":"og:image:height","content":"630"}],["$","meta","13",{"property":"og:image:alt","content":"How Claude Code Memory Actually Works"}],["$","meta","14",{"property":"og:type","content":"article"}],["$","meta","15",{"property":"article:published_time","content":"2026-03-21"}],["$","meta","16",{"name":"twitter:card","content":"summary_large_image"}],["$","meta","17",{"name":"twitter:title","content":"How Claude Code Memory Actually Works | Edgeless Lab"}],["$","meta","18",{"name":"twitter:description","content":"Claude forgets everything between sessions. File-based memory fixes that. The simplest setup, and why it changes how you work with AI."}],["$","meta","19",{"name":"twitter:image","content":"https://edgelesslab.com/og-image.webp"}],["$","link","20",{"rel":"icon","href":"/favicon.svg"}],["$","link","21",{"rel":"apple-touch-icon","href":"/apple-touch-icon.png"}],["$","$L1c","22",{}]]}]}]}],["$","meta",null,{"name":"next-size-adjust","content":""}]]}]
e:["$","$1","c",{"children":[null,["$","$L1d",null,{"parallelRouterKey":"children","template":["$","$L1e",null,{}]}]]}]
11:["$","$1","c",{"children":[null,["$","$L1d",null,{"parallelRouterKey":"children","template":["$","$L1e",null,{}]}]]}]
14:true
19:null
b:300
b:C
13:0
d:"$undefined"
f:"$undefined"
12:"$undefined"
a:"$undefined"
