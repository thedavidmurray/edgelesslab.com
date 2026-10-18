module.exports=[70406,(e,t,r)=>{t.exports=e.x("next/dist/compiled/@opentelemetry/api",()=>require("next/dist/compiled/@opentelemetry/api"))},18622,(e,t,r)=>{t.exports=e.x("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js",()=>require("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js"))},56704,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-async-storage.external.js",()=>require("next/dist/server/app-render/work-async-storage.external.js"))},32319,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-unit-async-storage.external.js",()=>require("next/dist/server/app-render/work-unit-async-storage.external.js"))},59043,(e,t,r)=>{t.exports=e.x("next/dist/server/runtime-reacts.external.js",()=>require("next/dist/server/runtime-reacts.external.js"))},93695,(e,t,r)=>{t.exports=e.x("next/dist/shared/lib/no-fallback-error.external.js",()=>require("next/dist/shared/lib/no-fallback-error.external.js"))},81111,(e,t,r)=>{t.exports=e.x("node:stream",()=>require("node:stream"))},30214,e=>{"use strict";var t=e.i(82085),r=e.i(45966);let a="https://edgelesslab.com";function s(e){return e.replace(/\r?\n+/g," ").trim()}async function n(){let e=[...t.posts].sort((e,t)=>new Date(t.date).getTime()-new Date(e.date).getTime()),n=e.slice(0,12),i=e.filter(e=>e.editorial),o=r.products.filter(e=>!e.comingSoon),l=o.filter(e=>"Free"===e.price).length,d=o.length-l,u=o.slice(0,20),p=r.projects.filter(e=>"Draft"!==e.status),c=r.experiments.filter(e=>"Draft"!==e.status),h=(e,t)=>{let r=`${a}/blog/${e.slug}`,n=e.description?`: ${s(e.description)}`:"";return`- [${s(e.title)}](${r}) (${e.date}, ${t})${n}`},m=e=>{let t=e.href||(e.slug?`${a}/projects/${e.slug}`:a),r=e.category?` [${e.category}]`:"";return`- [${s(e.title)}](${t})${r} (${e.status}): ${s(e.description)}`};return new Response(`# Edgeless Lab

> A public research studio for autonomous software, generative systems, and physical artifacts. Working systems, Field Notes, and methods published in the open. ${l} resources are free and ${d} deeper toolkits are paid.

## Docs

- [About](${a}/about): founder context, mission, and operating principles
- [Projects](${a}/projects): shipped and live systems
- [Agents](${a}/agents): multi-agent orchestration stack
- [Lab](${a}/lab): interactive playgrounds and experiments
- [Field Notes](${a}/field-notes): interactive studies, cited science plots, generative systems, and visual research
- [Services / Private AI Systems](${a}/services/private-ai-systems): custom private AI agent systems for professionals and small businesses
- [Agentic OS series](${a}/series/agentic-os): long-form series on building autonomous AI infrastructure
- [Knowledge](${a}/knowledge): KB index
- [Support](${a}/support): help and contact

## Recent posts

${n.map(e=>h(e,e.editorial?"editorial":"field-note")).join("\n")}

## Editorial (long-form)

${i.slice(0,12).map(e=>h(e,"editorial")).join("\n")}

## Products

${u.map(e=>{let t=e.price&&"Free"!==e.price?`, ${e.price}`:"",r=e.href||`${a}/products/${e.slug||""}`;return`- [${s(e.name)}](${r})${t}: ${s(e.description)}`}).join("\n")}

## Live projects

${p.map(m).join("\n")}

## Live experiments

${c.map(m).join("\n")}

## Related properties

- [Shop](https://shop.edgelesslab.com): art-led editions and physical objects from the lab

## Optional

- [RSS feed](${a}/feed.xml)
- [Sitemap](${a}/sitemap.xml)
- [Source on GitHub](https://github.com/edgeless-ai)

## Contact

- GitHub: https://github.com/edgeless-ai
- Site: https://edgelesslab.com
`,{headers:{"Content-Type":"text/plain; charset=utf-8","Cache-Control":"public, max-age=3600, s-maxage=3600"}})}e.s(["GET",0,n,"dynamic",0,"force-static"])},86793,e=>{"use strict";var t=e.i(67510),r=e.i(66881),a=e.i(77866),s=e.i(81911),n=e.i(22744),i=e.i(33802),o=e.i(59823),l=e.i(63193),d=e.i(1230),u=e.i(68548),p=e.i(55330),c=e.i(81459),h=e.i(97632),m=e.i(2459),g=e.i(93964),x=e.i(93695);e.i(79814);var v=e.i(43545);let f=new t.AppRouteRouteModule({definition:{kind:r.RouteKind.APP_ROUTE,page:"/llms.txt/route",pathname:"/llms.txt",filename:"route",bundlePath:""},distDir:".next",relativeProjectDir:"",resolvedPagePath:"[project]/src/app/llms.txt/route.ts",nextConfigOutput:"export",userland:()=>e.r(30214),...{}}),{workAsyncStorage:R,workUnitAsyncStorage:b,serverHooks:w}=f;async function y(e,t,a){a.requestMeta&&(0,s.setRequestMeta)(e,a.requestMeta),f.isDev&&(0,s.addRequestMeta)(e,"devRequestTimingInternalsEnd",process.hrtime.bigint());let R="/llms.txt/route";R=R.replace(/\/index$/,"")||"/";let b=await f.prepare(e,t,{srcPage:R,multiZoneDraftMode:!1});if(!b)return t.statusCode=400,t.end("Bad Request"),null==a.waitUntil||a.waitUntil.call(a,Promise.resolve()),null;let{buildId:w,deploymentId:y,params:$,nextConfig:E,parsedUrl:C,isDraftMode:A,prerenderManifest:S,routerServerContext:T,isOnDemandRevalidate:P,revalidateOnlyGenerated:j,resolvedPathname:q,clientReferenceManifest:N,serverActionsManifest:k}=b,O=(0,o.normalizeAppPath)(R),_=!!(S.dynamicRoutes[O]||S.routes[q]),H=async()=>((null==T?void 0:T.render404)?await T.render404(e,t,C,!1):t.end("This page could not be found"),null);if(_&&!A){let e=!!S.routes[q],t=S.dynamicRoutes[O];if(t&&!1===t.fallback&&!e){if(E.adapterPath)return await H();throw new x.NoFallbackError}}let I=null;!_||f.isDev||A||(I="/index"===(I=q)?"/":I);let D=!0===f.isDev||!_,M=_&&!D;k&&N&&(0,i.setManifestsSingleton)({page:R,clientReferenceManifest:N,serverActionsManifest:k});let U=e.method||"GET",F=(0,n.getTracer)(),L=F.getActiveScopeSpan(),K=!!(null==T?void 0:T.isWrappedByNextServer),G=!!(0,s.getRequestMeta)(e,"minimalMode"),B=(0,s.getRequestMeta)(e,"incrementalCache")||await f.getIncrementalCache(e,E,S,G);null==B||B.resetRequestCache(),globalThis.__incrementalCache=B;let V={params:$,previewProps:S.preview,renderOpts:{experimental:{authInterrupts:!!E.experimental.authInterrupts,useCacheTimeout:E.experimental.useCacheTimeout},cacheComponents:!!E.cacheComponents,validationLevel:E.experimental.instantInsights.validationLevel,supportsDynamicResponse:D,incrementalCache:B,hmrRefreshHash:(0,s.getRequestMeta)(e,"hmrRefreshHash"),cacheLifeProfiles:E.cacheLife,staticPageGenerationTimeout:E.staticPageGenerationTimeout,waitUntil:a.waitUntil,onClose:e=>{t.on("close",e)},onAfterTaskError:void 0,onInstrumentationRequestError:(t,r,a,s)=>f.onRequestError(e,t,a,s,T)},sharedContext:{buildId:w,deploymentId:y}},W=new l.NodeNextRequest(e),X=new l.NodeNextResponse(t),z=d.NextRequestAdapter.fromNodeNextRequest(W,(0,d.signalFromNodeResponse)(t)),Z=async({previousCacheEntry:r})=>{try{if(!G&&P&&j&&!r)return t.statusCode=404,t.setHeader("x-nextjs-cache","REVALIDATED"),t.end("This page could not be found"),null;let s=await f.handle(z,V);e.fetchMetrics=V.renderOpts.fetchMetrics;let n=V.renderOpts.pendingWaitUntil;n&&a.waitUntil&&(a.waitUntil(n),n=void 0);let i=V.renderOpts.collectedTags;if(!_)return await (0,c.sendResponse)(W,X,s,n),null;{let e=await s.blob(),t=(0,h.toNodeOutgoingHttpHeaders)(s.headers);i&&(t[g.NEXT_CACHE_TAGS_HEADER]=i),!t["content-type"]&&e.type&&(t["content-type"]=e.type);let r=void 0!==V.renderOpts.collectedRevalidate&&!(V.renderOpts.collectedRevalidate>=g.INFINITE_CACHE)&&V.renderOpts.collectedRevalidate,a=void 0===V.renderOpts.collectedExpire||V.renderOpts.collectedExpire>=g.INFINITE_CACHE?!1!==r&&r>0?E.expireTime:void 0:V.renderOpts.collectedExpire;return{value:{kind:v.CachedRouteKind.APP_ROUTE,status:s.status,body:Buffer.from(await e.arrayBuffer()),headers:t},cacheControl:{revalidate:r,expire:a}}}}catch(t){throw(null==r?void 0:r.isStale)&&await f.onRequestError(e,t,{routerKind:"App Router",routePath:R,routeType:"route",revalidateReason:(0,p.getRevalidateReason)({isStaticGeneration:M,isOnDemandRevalidate:P})},!1,T),t}},J=async(s,i)=>{try{var o,l;let s=await f.handleResponse({req:e,nextConfig:E,cacheKey:I,routeKind:r.RouteKind.APP_ROUTE,isFallback:!1,prerenderManifest:S,isRoutePPREnabled:!1,isOnDemandRevalidate:P,revalidateOnlyGenerated:j,responseGenerator:Z,waitUntil:a.waitUntil,isMinimalMode:G});if(!_)return;if((null==s||null==(o=s.value)?void 0:o.kind)!==v.CachedRouteKind.APP_ROUTE)throw Object.defineProperty(Error(`Invariant: app-route received invalid cache entry ${null==s||null==(l=s.value)?void 0:l.kind}`),"__NEXT_ERROR_CODE",{value:"E701",enumerable:!1,configurable:!0});G||t.setHeader("x-nextjs-cache",P?"REVALIDATED":s.isMiss?"MISS":s.isStale?"STALE":"HIT"),A&&t.setHeader("Cache-Control","private, no-cache, no-store, max-age=0, must-revalidate");let n=(0,h.fromNodeOutgoingHttpHeaders)(s.value.headers);G&&_||n.delete(g.NEXT_CACHE_TAGS_HEADER),!s.cacheControl||t.getHeader("Cache-Control")||n.get("Cache-Control")||n.set("Cache-Control",(0,m.getCacheControlHeader)(s.cacheControl)),await (0,c.sendResponse)(W,X,new Response(s.value.body,{headers:n,status:s.value.status||200}));return}catch(t){if(t instanceof x.NoFallbackError||await f.onRequestError(e,t,{routerKind:"App Router",routePath:O,routeType:"route",revalidateReason:(0,p.getRevalidateReason)({isStaticGeneration:M,isOnDemandRevalidate:P})},!1,T),_)throw t;await (0,c.sendResponse)(W,X,new Response(null,{status:500}));return}finally{(()=>{if(!s)return;let e=t.statusCode;s.setAttributes({"http.status_code":e,"next.rsc":!1}),e&&e>=500&&(s.setStatus({code:n.SpanStatusCode.ERROR}),s.setAttribute("error.type",e.toString()));let r=F.getRootSpanAttributes();if(!r)return;if(r.get("next.span_type")!==u.BaseServerSpan.handleRequest)return console.warn(`Unexpected root span type '${r.get("next.span_type")}'. Please report this Next.js issue https://github.com/vercel/next.js`);let a=r.get("next.route")||O,o=`${U} ${a}`;s.setAttributes({"next.route":a,"http.route":a,"next.span_name":o}),s.updateName(o),i&&i!==s&&(i.setAttribute("http.route",a),i.updateName(o))})()}};if(K&&L)await J(L,void 0);else{let t=F.getActiveScopeSpan();await F.withPropagatedContext(e.headers,()=>F.trace(u.BaseServerSpan.handleRequest,{spanName:`${U} ${R}`,kind:n.SpanKind.SERVER,attributes:{"http.method":U,"http.target":e.url}},e=>J(e,t)),void 0,!K)}}e.s(["handler",0,y,"patchFetch",0,function(){return(0,a.patchFetch)({workAsyncStorage:R,workUnitAsyncStorage:b})},"routeModule",0,f,"serverHooks",0,w,"workAsyncStorage",0,R,"workUnitAsyncStorage",0,b])}];

//# sourceMappingURL=%5Broot-of-the-server%5D__15v2omk._.js.map