// ---- state ----------------------------------------------------------------
const state = { pitch:null, imageFile:null, enhancedUrl:null, uploaded:null,
                brand:null, history:[], lineChart:null, barChart:null };

const $ = (s) => document.querySelector(s);
const el = (t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;};
const esc = (s)=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const money = (n)=>"$"+Math.round(n).toLocaleString();

function toast(m){const t=$("#toast");t.textContent=m;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),3600);}
function busy(b,on,l){b.disabled=on;b.dataset.t=b.dataset.t||b.textContent;b.innerHTML=on?`<span class="spinner"></span>${l||"Working…"}`:b.dataset.t;}
async function api(path,body){
  const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.detail||`Request failed (${r.status})`);}
  return r.json();
}

const CRUMBS={leads:["Leads","Find brands worth pitching"],research:["Research","Competitive gaps & product fit"],
  practice:["Practice","Rehearse against the AI buyer"],studio:["Studio","Enhance product image & video"],
  forecast:["Forecast","The growth you unlock for them"]};

document.querySelectorAll(".nav-item").forEach(b=>b.onclick=()=>{
  document.querySelectorAll(".nav-item").forEach(n=>n.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  b.classList.add("active");$("#tab-"+b.dataset.tab).classList.add("active");
  $("#crumb").textContent=CRUMBS[b.dataset.tab][0];$("#crumbSub").textContent=CRUMBS[b.dataset.tab][1];
});
function goTab(n){document.querySelector(`.nav-item[data-tab="${n}"]`).click();}

function syncState(){
  $("#ctxBrand").textContent=state.brand||"— none —";
  const has=!!state.pitch;
  [["#practiceEmpty","#practiceArea"],["#studioEmpty","#studioArea"],["#fcEmpty","#fcArea"]]
    .forEach(([e,a])=>{$(e).classList.toggle("hidden",has);$(a).classList.toggle("hidden",!has);});
}

// ---- 1. LEADS -------------------------------------------------------------
$("#findLeads").onclick=async(e)=>{
  const icp=$("#icp").value.trim();if(!icp)return toast("Describe an ICP first.");
  busy(e.target,true,"Finding leads…");
  try{
    const d=await api("/api/leads",{icp,count:6});const box=$("#leadsResult");box.innerHTML="";
    (d.leads||[]).forEach(l=>{
      const c=el("div","lead",`<span class="score">${Math.round(l.fit_score)}</span>
        <h3>${esc(l.brand)}</h3><div class="meta">${esc(l.category||"")} · ${esc(l.market||"")}</div>
        <div class="reason">${esc(l.reason||"")}</div>`);
      const b=el("button","btn primary","Research →");
      b.onclick=()=>{$("#brandInput").value=l.brand;goTab("research");$("#runResearch").click();};
      c.appendChild(b);box.appendChild(c);
    });
    if(!(d.leads||[]).length)toast("No leads returned — try a more specific ICP.");
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

// ---- 2. RESEARCH ----------------------------------------------------------
$("#runResearch").onclick=async(e)=>{
  const brand=$("#brandInput").value.trim();if(!brand)return toast("Enter a brand name.");
  busy(e.target,true,"Analysing…");
  try{
    const p=await api("/api/research",{brand});
    state.pitch=p;state.brand=p.brand||brand;
    state.imageFile=null;state.enhancedUrl=null;state.uploaded=null;state.history=[];
    ["#imageWrap","#videoWrap","#chat","#coachPanel","#suggestPanel","#assetPreview"].forEach(id=>$(id).innerHTML="");
    $("#genImage").disabled=true;$("#genVideo").disabled=true;$("#dropText").textContent="Click to choose a product photo (JPG / PNG)";
    renderResearch(p);syncState();
    toast("Analysis ready. Practice the pitch or open Studio from the sidebar.");
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

function renderResearch(p){
  const box=$("#researchResult");box.innerHTML="";
  box.appendChild(el("div","section-title","WHO THEY ARE"));
  box.appendChild(el("div","prose",esc(p.brand_summary)));
  box.appendChild(el("div","section-title","COMPETITIVE POSITION"));
  box.appendChild(el("div","prose",esc(p.competitive_position)));
  box.appendChild(el("div","section-title","KEY COMPETITORS"));
  const ch=el("div","chips");(p.likely_competitors||[]).forEach(c=>ch.appendChild(el("span","chip",esc(c))));box.appendChild(ch);
  box.appendChild(el("div","section-title","GAPS"));
  const g=el("div","grid");(p.gaps||[]).forEach(x=>{const s=(x.severity||"medium").toLowerCase();
    g.appendChild(el("div","gapcard",`<span class="badge ${s}">${s.toUpperCase()}</span><h4>${esc(x.gap)}</h4><p>${esc(x.why_it_matters)}</p>`));});box.appendChild(g);
  box.appendChild(el("div","section-title","HOW ANYMIND CLOSES THE GAPS"));
  (p.solution_mapping||[]).forEach(m=>box.appendChild(el("div","solrow",
    `<div class="pill">${esc(m.product)}</div><div class="ga">${esc(m.gap_addressed)}</div><div class="hh">${esc(m.how_it_helps)}</div>`)));
  const imp=p.projected_impact||{},rev=imp.revenue_or_profit_uplift||{},eff=imp.time_or_efficiency_gain||{};
  box.appendChild(el("div","section-title","PROJECTED IMPACT"));
  box.appendChild(el("div","stats",
    `<div class="stat"><div class="big">${esc(rev.low)}–${esc(rev.high)}</div><div class="lbl">Revenue / profit uplift</div><div class="sub">${esc(rev.basis)} (${esc(rev.timeframe)})</div></div>
     <div class="stat"><div class="big">${esc(eff.low)}–${esc(eff.high)}</div><div class="lbl">Time / efficiency gain</div><div class="sub">${esc(eff.what_it_speeds_up)}</div></div>
     <div class="stat"><div class="big">${esc(imp.time_to_value)}</div><div class="lbl">Time to value</div><div class="sub">From kickoff to measurable results.</div></div>`));
  const pkg=p.recommended_package||{};
  box.appendChild(el("div","pkg",`<div class="kicker">RECOMMENDED PACKAGE</div><h3>${esc(pkg.package_name)}</h3>
    <p>${esc(pkg.rationale)}</p><div class="chips">${(pkg.included_products||[]).map(x=>`<span class="chip">${esc(x)}</span>`).join("")}</div>`));
}

// ---- 3. PRACTICE ----------------------------------------------------------
function addMsg(role,text){const m=el("div","msg "+role,esc(text));$("#chat").appendChild(m);$("#chat").scrollTop=$("#chat").scrollHeight;}
async function sendRep(){
  const inp=$("#repMsg"),text=inp.value.trim();if(!text||!state.pitch)return;
  $("#buyerName").textContent=(state.brand||"The brand")+" — CMO";
  addMsg("rep",text);state.history.push({role:"rep",content:text});inp.value="";
  const btn=$("#sendMsg");busy(btn,true,"…");
  try{
    const r=await api("/api/roleplay",{pitch:state.pitch,history:state.history.slice(0,-1),message:text});
    addMsg("buyer",r.reply);state.history.push({role:"buyer",content:r.reply});
  }catch(err){toast(err.message);}
  busy(btn,false);
}
$("#sendMsg").onclick=sendRep;
$("#repMsg").addEventListener("keydown",e=>{if(e.key==="Enter")sendRep();});

$("#coachBtn").onclick=async(e)=>{
  if(state.history.length<2)return toast("Have a short exchange first.");
  busy(e.target,true,"Scoring…");
  try{
    const f=await api("/api/roleplay/feedback",{pitch:state.pitch,history:state.history});
    $("#coachPanel").innerHTML=`<div class="panel coach">
      <div class="coach-score">${Math.round(f.score)}/100</div>
      <h4>WHAT WORKED</h4><ul>${(f.what_worked||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      <h4>WHAT TO IMPROVE</h4><ul>${(f.what_to_improve||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      <h4>MISSED OBJECTIONS</h4><ul>${(f.missed_objections||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      <h4>TRY NEXT</h4><div class="prose">${esc(f.one_thing_to_try_next)}</div></div>`;
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

$("#suggestBtn").onclick=async(e)=>{
  if(!state.pitch)return;busy(e.target,true,"Thinking…");
  try{
    const s=await api("/api/roleplay/suggest",{pitch:state.pitch,history:state.history});
    $("#suggestPanel").innerHTML=`<div class="suggest">
      <div class="suggest-head">SUGGESTED LINE <button class="btn tiny" id="useSuggest">Use it</button></div>
      <div class="suggest-line">${esc(s.suggested_line)}</div>
      <div class="suggest-tp">${(s.talking_points||[]).map(t=>`<span class="chip">${esc(t)}</span>`).join("")}</div>
      <div class="suggest-why">${esc(s.why||"")}</div></div>`;
    $("#useSuggest").onclick=()=>{$("#repMsg").value=s.suggested_line;$("#repMsg").focus();};
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

// ---- 4. STUDIO (upload -> enhance -> video) -------------------------------
$("#assetInput").onchange=(e)=>{
  const f=e.target.files[0];if(!f)return;const r=new FileReader();
  r.onload=()=>{
    state.uploaded=r.result;state.enhancedUrl=null;
    $("#assetPreview").innerHTML=`<img src="${r.result}" alt="product"/>`;
    $("#dropText").textContent=f.name;
    $("#genImage").disabled=false;$("#genVideo").disabled=true;$("#videoWrap").innerHTML="";
  };
  r.readAsDataURL(f);
};

$("#genImage").onclick=async(e)=>{
  if(!state.pitch||!state.uploaded)return toast("Upload a product image first.");
  busy(e.target,true,"Enhancing…");
  try{
    const r=await api("/api/image",{pitch:state.pitch,init_image:state.uploaded});
    state.imageFile=r.image_file;state.enhancedUrl=r.image_remote_url;
    $("#imageWrap").innerHTML=`<div class="ba"><figure><figcaption>Original</figcaption><img src="${state.uploaded}"/></figure>
      <figure><figcaption>Enhanced</figcaption><img src="${r.image_url}"/></figure></div>`;
    if(state.enhancedUrl){$("#genVideo").disabled=false;toast("Enhanced. You can now create the product video.");}
    else toast("Enhanced, but no public URL returned — video needs one.");
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

$("#genVideo").onclick=async(e)=>{
  if(!state.enhancedUrl)return toast("Enhance the image first — the video animates the enhanced image.");
  busy(e.target,true,"Rendering video (1–2 min)…");
  try{
    const r=await api("/api/video",{pitch:state.pitch,init_image:state.enhancedUrl});
    $("#videoWrap").innerHTML=`<video src="${r.video_url}" controls autoplay muted loop playsinline></video>`;
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

$("#buildDeck").onclick=async(e)=>{
  if(!state.pitch)return;busy(e.target,true,"Building deck…");
  try{
    const r=await api("/api/deck",{pitch:state.pitch,image_file:state.imageFile});
    const a=document.createElement("a");a.href=r.deck_url;a.download="";a.click();toast("Deck downloaded.");
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

// ---- 5. FORECAST ----------------------------------------------------------
$("#runForecast").onclick=async(e)=>{
  if(!state.pitch)return;busy(e.target,true,"Projecting…");
  try{
    const d=await api("/api/forecast",{pitch:state.pitch,assumptions:{
      start_revenue:+$("#startRev").value,organic_growth:+$("#organic").value,months:+$("#fcMonths").value}});
    renderForecast(d);
  }catch(err){toast(err.message);}
  busy(e.target,false);
};

function renderForecast(d){
    const fmtAxis=v=>{
  if(Math.abs(v)>=1e6) return "$"+(v/1e6).toFixed(1)+"M";
  if(Math.abs(v)>=1e3) return "$"+Math.round(v/1e3)+"k";
  return "$"+Math.round(v);
};
  const best=d.strategies.find(s=>s.strategy===d.recommended);
  $("#fcHeadline").innerHTML=`With the <b>${esc(best.label)}</b> path, ${esc(d.brand)} could unlock
    <b>${money(best.uplift_vs_baseline)}</b> in extra revenue over ${d.assumptions.horizon_months} months — a ${best.uplift_pct}% lift vs. doing nothing.`;
  const cards=$("#fcCards");cards.innerHTML="";
  d.strategies.forEach(s=>{
    const b=s.strategy===d.recommended;
    cards.appendChild(el("div","stratcard"+(b?" best":""),
      `${b?'<span class="tag">BEST UPLIFT</span>':""}<h3>${esc(s.label)}</h3>
       <div class="total">${money(s.total_revenue)}</div>
       <div class="uplift">+${money(s.uplift_vs_baseline)} vs baseline (${s.uplift_pct}%)</div>
       <div class="blurb">${esc(s.blurb)}</div>`));
  });
  const labels=d.baseline.monthly_revenue.map((_,i)=>"M"+(i+1));
  const C={"Quick Win":"#0B8C9B","Full Transformation":"#22D3A8","Phased Rollout":"#0F1E2E"};
  const ds=[{label:"Do nothing (baseline)",data:d.baseline.monthly_revenue,borderColor:"#B6C4CC",borderDash:[5,4],backgroundColor:"transparent",tension:.3,pointRadius:0,borderWidth:2},
    ...d.strategies.map(s=>({label:s.label,data:s.monthly_revenue,borderColor:C[s.label]||"#0B8C9B",backgroundColor:"transparent",tension:.3,pointRadius:0,borderWidth:2}))];
  if(state.lineChart)state.lineChart.destroy();
  state.lineChart=new Chart($("#lineChart"),{type:"line",data:{labels,datasets:ds},
    options:{responsive:true,plugins:{legend:{position:"bottom"}},scales:{y:{ticks:{callback:fmtAxis}}}}});
  if(state.barChart)state.barChart.destroy();
  state.barChart=new Chart($("#barChart"),{type:"bar",
    data:{labels:d.strategies.map(s=>s.label),datasets:[{data:d.strategies.map(s=>s.uplift_vs_baseline),
      backgroundColor:d.strategies.map(s=>C[s.label]||"#0B8C9B")}]},
    options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:fmtAxis}}}}});
}

syncState();