1:"$Sreact.fragment"
2:I[56850,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],"Nav"]
3:I[65303,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],"BlogArticle"]
4:T2753,<h1>Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One</h1>
<p><strong>Published:</strong> April 2026   <strong>Reading time:</strong> 10 minutes   <strong>Author:</strong> Scribe (Edgeless Labs)</p>
<p>---</p>
<h2 id="the-wrong-way-to-scale-ai">The Wrong Way to Scale AI</h2>
<p>When I started building agent systems, I made the same mistake everyone does:</p>
<blockquote>"If Claude 4 is good, Claude 4 for everything must be better."</blockquote>
<p>Wrong.</p>
<p>Using the most powerful model for every task is like hiring a brain surgeon to answer your emails. Technically capable? Yes. Economically sane? Absolutely not.</p>
<p>My first month running a 10-agent system:</p>
<ul><li><strong>API bill:</strong> $847</li><li><strong>Latency:</strong> 8.2s average response</li><li><strong>Overkill rate:</strong> 73% (simple tasks on flagship model)</li></ul>
<p>I was burning money and patience. Time to rethink.</p>
<p>---</p>
<h2 id="the-economics-of-model-selection">The Economics of Model Selection</h2>
<p>Modern LLMs aren't just "better" or "worse." They're specialized labor markets with different hourly rates.</p>
<p>| Model | Provider | Input/1M | Output/1M | Strengths | My Use Case | |-------|----------|----------|-----------|-------------|-------------| | <strong>Kimi K2.5</strong> | Fireworks | $0.70 | $2.80 | Long context, tool use | Agent orchestration, skills | | <strong>DeepSeek V3.2</strong> | Fireworks | $0.40 | $1.60 | Reasoning, code | Analysis, math, structured output | | <strong>Codex GPT-5.4</strong> | OpenAI | $3.00 | $12.00 | Code synthesis | Code generation, diff review | | <strong>Claude Opus 4</strong> | Anthropic | $15.00 | $75.00 | Complex reasoning | Research synthesis, edge cases |</p>
<p>Claude Opus costs <strong>26x more</strong> than Kimi K2.5 for output. Use it wisely.</p>
<p>---</p>
<h2 id="the-router-mastra">The Router: Mastra</h2>
<p>Instead of hardcoding model choices, I built a routing layer that selects based on task characteristics.</p>
<pre><code># /etc/paperclip/model-routing.yaml
models:
  kimi-k2p5-fireworks:
    provider: fireworks
    model: accounts/fireworks/models/kimi-k2p5
    cost_input: 0.70
    cost_output: 2.80
    context_window: 256000
    tool_capable: true
    default_for: [skills, orchestration, terminal]
    
  deepseek-v3p2-fireworks:
    provider: fireworks
    model: accounts/fireworks/models/deepseek-v3p2
    cost_input: 0.40
    cost_output: 1.60
    reasoning: strong
    default_for: [analysis, math, json_output]
    
  codex-gpt-5-4:
    provider: openai
    model: gpt-5.4-codex
    cost_input: 3.00
    cost_output: 12.00
    code_capable: true
    default_for: [code_generation, code_review, patches]
    
  claude-opus-4:
    provider: anthropic
    model: claude-opus-4-6
    cost_input: 15.00
    cost_output: 75.00
    complex_reasoning: true
    override_when:
      - task_contains: "research synthesis"
      - task_contains: "deep analysis"
      - estimated_tokens: "&gt;4000"</code></pre>
<p>---</p>
<h2 id="routing-logic">Routing Logic</h2>
<p>The router doesn't just look at task type. It considers:</p>
<h3>1. Estimated Complexity</h3>
<pre><code># From the routing engine
def estimate_complexity(task_description: str) -&gt; int:
    """
    1-10 scale based on:
    - Output length estimation
    - Reasoning depth signals
    - Tool call requirements
    - Context window needs
    """
    signals = {
        'high_complexity': ['synthesize', 'research', 'compare', 'evaluate'],
        'medium_complexity': ['summarize', 'explain', 'format'],
        'low_complexity': ['classify', 'extract', 'transform']
    }
    # ... scoring logic</code></pre>
<h3>2. Tool Requirements</h3>
<p>Kimi K2.5 and DeepSeek support native tool use. Codex and Claude Opus don't (in the same way). If a task needs terminal/browser/file tools, the router eliminates non-tool-capable models immediately.</p>
<h3>3. Context Window</h3>
<p>| Task | Tokens | Suitable Models | |------|--------|-----------------| | Skill execution | 2K-8K | All | | Code review (large file) | 15K-30K | Kimi, DeepSeek | | Research synthesis | 50K+ | Kimi (256K window) |</p>
<p>A 100K token task on Claude Opus would cost <strong>$7.50</strong> just for input. On Kimi: <strong>$0.07</strong>.</p>
<h3>4. Latency Budget</h3>
<p>Some tasks have time constraints:</p>
<pre><code>routing_rules:
  - if: latency_required &lt; 2000ms
    then: use_local_model  # llama-cpp on M3 Max
    
  - if: latency_required &lt; 5000ms
    then: prefer: [kimi, deepseek]
    
  - if: quality_critical: true
    then: allow: [claude-opus, codex]
    cost_threshold: ignore</code></pre>
<p>---</p>
<h2 id="real-routing-decisions">Real Routing Decisions</h2>
<p>Here are actual routing choices from my system this week:</p>
<p>| Task | Routed To | Cost | Time | Why | |------|-----------|------|------|-----| | "Check 5 RSS feeds, summarize new items" | Kimi K2.5 | $0.003 | 2.1s | Tool use, parallel, cheap | | "Review this git diff for bugs" | Codex GPT-5.4 | $0.08 | 4.2s | Code-trained, diff format | | "Synthesize 3 research papers into principles" | Claude Opus | $1.20 | 12s | Complex synthesis, 8K output | | "Convert CSV to JSON with validation" | DeepSeek V3.2 | $0.001 | 1.4s | Structured output, reasoning | | "Generate blog post from notes" | Kimi K2.5 | $0.04 | 5.8s | Long output, tool templates |</p>
<p><strong>Weekly routing distribution:</strong></p>
<ul><li>Kimi K2.5: 67% of tasks ($0.70/1M input)</li><li>DeepSeek V3.2: 24% of tasks ($0.40/1M input)</li><li>Codex GPT-5.4: 7% of tasks ($3.00/1M input)</li><li>Claude Opus: 2% of tasks ($15.00/1M input)</li></ul>
<p><strong>Result:</strong> 10x cost reduction vs. using Claude Opus for everything. Same (often better) quality because tasks match model strengths.</p>
<p>---</p>
<h2 id="the-configuration-file">The Configuration File</h2>
<p>My complete production model routing config:</p>
<pre><code># model-routing.yaml - Production configuration
version: 1.2

providers:
  fireworks:
    base_url: https://api.fireworks.ai/inference/v1
    api_key_env: FIREWORKS_API_KEY
    timeout: 30
    
  openai:
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
    timeout: 45
    
  anthropic:
    base_url: https://api.anthropic.com/v1
    api_key_env: ANTHROPIC_API_KEY
    timeout: 60

models:
  # Workhorses (80% of traffic)
  kimi-k2p5:
    provider: fireworks
    model: accounts/fireworks/models/kimi-k2p5
    context: 256000
    max_output: 8192
    tool_format: openai
    default_for:
      - agent_conversation
      - skill_execution
      - terminal_operations
      - file_operations
      - web_extraction
    cost_per_1m_input: 0.70
    cost_per_1m_output: 2.80
    
  deepseek-v3p2:
    provider: fireworks
    model: accounts/fireworks/models/deepseek-v3p2
    context: 64000
    max_output: 8192
    structured_output: strong
    default_for:
      - analysis
      - calculations
      - json_generation
      - reasoning_tasks
    cost_per_1m_input: 0.40
    cost_per_1m_output: 1.60
    
  # Specialists (18% of traffic)
  codex-gpt-5-4:
    provider: openai
    model: gpt-5.4-codex
    context: 128000
    max_output: 8192
    code_specialist: true
    default_for:
      - code_generation
      - code_review
      - patch_application
      - terminal_debugging
    cost_per_1m_input: 3.00
    cost_per_1m_output: 12.00
    
  # Heavy lifters (2% of traffic)
  claude-opus-4-6:
    provider: anthropic
    model: claude-opus-4-6
    context: 200000
    max_output: 8192
    complex_reasoning: true
    override_when:
      - task_type: research_synthesis
      - task_type: complex_analysis
      - estimated_output_tokens: "&gt;6000"
    cost_per_1m_input: 15.00
    cost_per_1m_output: 75.00

routing_logic:
  # Primary: match task to default model
  default_selection: by_task_type
  
  # Secondary: complexity override
  complexity_thresholds:
    - if: score &gt; 8
      then: consider_claude_opus
      
  # Tertiary: latency requirements
  latency_budget:
    - if: required_ms &lt; 3000
      then: exclude_claude_opus
      
  # Emergency: all models down
  fallback_chain:
    - kimi-k2p5
    - deepseek-v3p2
    - local-llama-8b</code></pre>
<p>---</p>
<h2 id="measuring-router-performance">Measuring Router Performance</h2>
<p>I track two metrics:</p>
<h3>1. Cost Per Task</h3>
<pre><code>Daily average (last 30 days):
- Before routing: $28.40/day (all Claude Opus)
- After routing: $2.70/day (mixed)
- Savings: 90.5%</code></pre>
<h3>2. Quality Score</h3>
<p>Human review of 100 random outputs per week:</p>
<p>| Model | Satisfaction Score (1-5) | |-------|-------------------------| | Kimi K2.5 | 4.2 | | DeepSeek V3.2 | 4.3 | | Codex GPT-5.4 | 4.5 (code tasks) | | Claude Opus | 4.7 |</p>
<p>Interesting: <strong>DeepSeek V3.2 scores higher than Kimi on analysis tasks</strong> despite being cheaper. Model fit > model power.</p>
<p>---</p>
<h2 id="when-to-route-vs-when-to-upgrade">When to Route vs. When to Upgrade</h2>
<p>Routing works best when you have <strong>task diversity</strong>. If all your tasks are:</p>
<ul><li>Research synthesis → Use Claude Opus directly</li><li>Code generation → Use Codex directly</li><li>Mixed bag → Build a router</li></ul>
<p>The overhead of routing (latency, complexity) only pays off at scale. For 10+ agents doing varied work: essential. For 2 agents doing the same thing: overhead.</p>
<p>---</p>
<h2 id="next-post-3">Next: Post 3</h2>
<p>Routing saves money. But how do you prevent agents from losing context across sessions? </p>
<p><a href="/blog/knowledge-base-loop/">The Knowledge Base Loop →</a></p>
<p>---</p>
<h2 id="get-the-blueprint">Get the Blueprint</h2>
<p>Want the complete model routing configuration? It's included in:</p>
<ul><li><strong>Paperclip OS ($49):</strong> Full orchestration blueprint</li><li><strong>Hermes Deployment Guide ($19):</strong> Router setup, API server, cron templates</li><li><strong>Bundle ($79):</strong> All 3 products</li></ul>
<p>[gumroad.com/l/paperclip-os]</p>b:X
10:X
10:C
0:{"buildId":"ILG6gReoatO94noDnyNVS","data":[{"rsc":["$","$1","c",{"children":[["$","div",null,{"className":"flex flex-col min-h-full","style":{"background":"var(--bg-base)"},"children":[["$","$L2",null,{}],["$","script",null,{"type":"application/ld+json","dangerouslySetInnerHTML":{"__html":"{\"@context\":\"https://schema.org\",\"@type\":\"BlogPosting\",\"headline\":\"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One\",\"description\":\"My agent system routes requests across 4 models based on task type. Full cost breakdown, routing logic, and configuration. 10x cost reduction vs. single-model approach.\",\"datePublished\":\"2026-04-19\",\"dateModified\":\"2026-04-19\",\"wordCount\":2500,\"author\":{\"@type\":\"Person\",\"name\":\"David Murray\",\"url\":\"https://edgelesslab.com/about\"},\"publisher\":{\"@type\":\"Organization\",\"name\":\"Edgeless Lab\",\"url\":\"https://edgelesslab.com\"},\"url\":\"https://edgelesslab.com/blog/multi-model-routing\",\"keywords\":[\"AI Agents\",\"Model Routing\",\"Cost Optimization\",\"Multi-Agent\"],\"mainEntityOfPage\":{\"@type\":\"WebPage\",\"@id\":\"https://edgelesslab.com/blog/multi-model-routing\"}}"}}],["$","script",null,{"type":"application/ld+json","dangerouslySetInnerHTML":{"__html":"{\"@context\":\"https://schema.org\",\"@type\":\"BreadcrumbList\",\"itemListElement\":[{\"@type\":\"ListItem\",\"position\":1,\"name\":\"Home\",\"item\":\"https://edgelesslab.com\"},{\"@type\":\"ListItem\",\"position\":2,\"name\":\"Blog\",\"item\":\"https://edgelesslab.com/blog\"},{\"@type\":\"ListItem\",\"position\":3,\"name\":\"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One\",\"item\":\"https://edgelesslab.com/blog/multi-model-routing\"}]}"}}],["$","article",null,{"className":"pt-28 pb-20 px-6","children":["$","div",null,{"className":"max-w-[960px] mx-auto","children":[["$","div",null,{"className":"mb-12 max-w-[680px]","children":["$undefined",["$","div",null,{"className":"flex items-center gap-3 mb-4","children":[["$","time",null,{"className":"text-xs font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-04-19","children":"April 19, 2026"}],["$","span",null,{"className":"text-xs font-mono","style":{"color":"var(--text-tertiary)"},"children":"10 min"}]]}],["$","h1",null,{"className":"text-3xl sm:text-4xl font-bold tracking-tight leading-[1.2] mb-4","style":{"color":"var(--text-primary)"},"children":"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One"}],["$","p",null,{"className":"text-lg font-light","style":{"color":"var(--text-secondary)","lineHeight":1.7},"children":"My agent system routes requests across 4 models based on task type. Full cost breakdown, routing logic, and configuration. 10x cost reduction vs. single-model approach."}],["$","div",null,{"className":"flex flex-wrap gap-2 mt-4","children":[["$","span","AI Agents",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"AI Agents"}],["$","span","Model Routing",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"Model Routing"}],["$","span","Cost Optimization",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"Cost Optimization"}],["$","span","Multi-Agent",{"className":"px-2.5 py-1 text-xs font-mono rounded-md","style":{"background":"var(--accent-muted)","color":"var(--accent)"},"children":"Multi-Agent"}]]}],"$undefined"]}],["$","$L3",null,{"html":"$4","editorial":true}],false,"$L5",false,false,"$L6"]}]}],"$L7"]}],["$L8"],"$L9"]}],"isPartial":"$@a","staleTime":"$b","varyParams":null},{"rsc":"$Lc","isPartial":"$@d","staleTime":"$b","varyParams":null},{"rsc":"$Le","isPartial":"$@f","staleTime":"$b","varyParams":"$10"},{"rsc":"$L11","isPartial":"$@12","staleTime":"$b","varyParams":"$10"}],"isUpgradeableISRFallback":false,"a":"$@13","rootVaryParams":null,"needsRuntimeRequest":"$@14"}
15:I[15715,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],""]
16:I[35822,["/_next/static/chunks/2cue0t2y-yu_9.js","/_next/static/chunks/3x4v8a24_pq_9.js"],"Footer"]
17:I[1913,["/_next/static/chunks/2cue0t2y-yu_9.js"],"OutletBoundary"]
18:"$Sreact.suspense"
1a:I[1913,["/_next/static/chunks/2cue0t2y-yu_9.js"],"ViewportBoundary"]
1b:I[1913,["/_next/static/chunks/2cue0t2y-yu_9.js"],"MetadataBoundary"]
1c:I[50529,["/_next/static/chunks/2cue0t2y-yu_9.js"],"IconMark"]
1d:I[67593,["/_next/static/chunks/2cue0t2y-yu_9.js"],"default"]
1e:I[92370,["/_next/static/chunks/2cue0t2y-yu_9.js"],"default"]
5:["$","section",null,{"className":"mt-16 pt-8 border-t","style":{"borderColor":"var(--border-subtle)"},"aria-label":"Related posts","children":[["$","h2",null,{"className":"text-sm font-mono uppercase tracking-[0.1em] mb-6","style":{"color":"var(--text-tertiary)"},"children":"Related Posts"}],["$","div",null,{"className":"grid gap-4 sm:grid-cols-3","children":[["$","$L15","agentic-engineering-resource-collision",{"href":"/blog/agentic-engineering-resource-collision","className":"group block p-4 rounded-lg border transition-colors","style":{"background":"var(--bg-surface)","borderColor":"var(--border-subtle)"},"children":[["$","div",null,{"className":"text-sm font-semibold mb-1 transition-colors group-hover:text-white","style":{"color":"var(--text-primary)"},"children":"The Week Agentic Engineering's Hidden Crisis: Resource Collision"}],["$","div",null,{"className":"text-xs line-clamp-2","style":{"color":"var(--text-tertiary)","lineHeight":1.5},"children":"When N agents run in parallel they collide on ports, worktrees, databases, and token budgets — with no detection, isolation, or recovery. The binding constraint on parallel agent teams isn't model capability, it's resource allocation."}],["$","div",null,{"className":"flex items-center gap-2 mt-3","children":[["$","time",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-08-05","children":"Aug 2026"}],["$","span",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"children":"8 min"}]]}]]}],["$","$L15","verification-chain-crisis",{"href":"/blog/verification-chain-crisis","className":"group block p-4 rounded-lg border transition-colors","style":{"background":"var(--bg-surface)","borderColor":"var(--border-subtle)"},"children":[["$","div",null,{"className":"text-sm font-semibold mb-1 transition-colors group-hover:text-white","style":{"color":"var(--text-primary)"},"children":"The Verification Chain Crisis: Why Multi-Agent Systems Fail Invisible"}],["$","div",null,{"className":"text-xs line-clamp-2","style":{"color":"var(--text-tertiary)","lineHeight":1.5},"children":"Six videos, one week, one recurring failure mode: the cheapest node in your orchestration graph rots the whole output. The specific mechanical fixes from chained verification stacks to deliberative panels."}],["$","div",null,{"className":"flex items-center gap-2 mt-3","children":[["$","time",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-08-04","children":"Aug 2026"}],["$","span",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"children":"8 min"}]]}]]}],["$","$L15","agentic-engineering-week",{"href":"/blog/agentic-engineering-week","className":"group block p-4 rounded-lg border transition-colors","style":{"background":"var(--bg-surface)","borderColor":"var(--border-subtle)"},"children":[["$","div",null,{"className":"text-sm font-semibold mb-1 transition-colors group-hover:text-white","style":{"color":"var(--text-primary)"},"children":"The Week Agentic Engineering Became a Real Discipline"}],["$","div",null,{"className":"text-xs line-clamp-2","style":{"color":"var(--text-tertiary)","lineHeight":1.5},"children":"Nine YouTube videos, one week, zero hype. The shift from prompting to systems architecture is happening in plain sight — here's what it means for your agent stack."}],["$","div",null,{"className":"flex items-center gap-2 mt-3","children":[["$","time",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"dateTime":"2026-07-30","children":"Jul 2026"}],["$","span",null,{"className":"text-[10px] font-mono","style":{"color":"var(--text-tertiary)"},"children":"6 min"}]]}]]}]]}]]}]
6:["$","div",null,{"className":"mt-12 pt-8 border-t","style":{"borderColor":"var(--border-subtle)"},"children":["$","$L15",null,{"href":"/blog","className":"text-sm font-medium transition-colors hover:text-white","style":{"color":"var(--text-secondary)"},"children":"← All posts"}]}]
7:["$","$L16",null,{}]
8:["$","script","script-0",{"src":"/_next/static/chunks/3x4v8a24_pq_9.js","async":true}]
9:["$","$L17",null,{"children":["$","$18",null,{"name":"Next.MetadataOutlet","children":"$@19"}]}]
c:["$","$1","h",{"children":[null,["$","$L1a",null,{"children":[["$","meta","0",{"charSet":"utf-8"}],["$","meta","1",{"name":"viewport","content":"width=device-width, initial-scale=1"}]]}],["$","div",null,{"hidden":true,"children":["$","$L1b",null,{"children":["$","$18",null,{"name":"Next.Metadata","children":[["$","title","0",{"children":"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One | Edgeless Lab"}],["$","meta","1",{"name":"description","content":"My agent system routes requests across 4 models based on task type. Full cost breakdown, routing logic, and configuration. 10x cost reduction vs. single-model approach."}],["$","meta","2",{"name":"keywords","content":"AI Agents,Model Routing,Cost Optimization,Multi-Agent"}],["$","meta","3",{"name":"robots","content":"index, follow"}],["$","meta","4",{"name":"googlebot","content":"index, follow"}],["$","link","5",{"rel":"canonical","href":"https://edgelesslab.com/blog/multi-model-routing/"}],["$","meta","6",{"property":"og:title","content":"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One | Edgeless Lab"}],["$","meta","7",{"property":"og:description","content":"My agent system routes requests across 4 models based on task type. Full cost breakdown, routing logic, and configuration. 10x cost reduction vs. single-model approach."}],["$","meta","8",{"property":"og:url","content":"https://edgelesslab.com/blog/multi-model-routing/"}],["$","meta","9",{"property":"og:site_name","content":"Edgeless Lab"}],["$","meta","10",{"property":"og:image","content":"https://edgelesslab.com/og-image.webp"}],["$","meta","11",{"property":"og:image:width","content":"1200"}],["$","meta","12",{"property":"og:image:height","content":"630"}],["$","meta","13",{"property":"og:image:alt","content":"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One"}],["$","meta","14",{"property":"og:type","content":"article"}],["$","meta","15",{"property":"article:published_time","content":"2026-04-19"}],["$","meta","16",{"name":"twitter:card","content":"summary_large_image"}],["$","meta","17",{"name":"twitter:title","content":"Multi-Model Routing: Why I Run 4 Different AI Brains Instead of One | Edgeless Lab"}],["$","meta","18",{"name":"twitter:description","content":"My agent system routes requests across 4 models based on task type. Full cost breakdown, routing logic, and configuration. 10x cost reduction vs. single-model approach."}],["$","meta","19",{"name":"twitter:image","content":"https://edgelesslab.com/og-image.webp"}],["$","link","20",{"rel":"icon","href":"/favicon.svg"}],["$","link","21",{"rel":"apple-touch-icon","href":"/apple-touch-icon.png"}],["$","$L1c","22",{}]]}]}]}],["$","meta",null,{"name":"next-size-adjust","content":""}]]}]
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
