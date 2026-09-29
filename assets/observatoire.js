let DATA={offres:[],stats:{}};let chart;
const $=s=>document.querySelector(s);const fmt=n=>new Intl.NumberFormat("fr-FR").format(n||0);
function uniq(a){return [...new Set(a.filter(Boolean))].sort((x,y)=>x.localeCompare(y,"fr"))}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}
function optionList(el,values){for(const v of values){const o=document.createElement("option");o.value=v;o.textContent=v;el.appendChild(o)}}
function current(){
 const q=$("#q").value.trim().toLowerCase(),src=$("#source").value,ct=$("#contrat").value,remote=$("#remote").checked;
 return DATA.offres.filter(o=>{
   const hay=[o.titre,o.entreprise,o.ville,o.description,...(o.competences||[])].join(" ").toLowerCase();
   return (!q||hay.includes(q))&&(!src||(o.sources||[]).includes(src))&&(!ct||o.contrat===ct)&&(!remote||o.teletravail);
 });
}
function renderJobs(list){
 $("#nb-resultats").textContent=fmt(list.length)+" résultat"+(list.length>1?"s":"");
 $("#k-filtres").textContent=fmt(list.length);
 $("#offres").innerHTML=list.length?list.slice(0,120).map(o=>{
  const sources=(o.sources||[o.source_label]).map(s=>'<span class="badge source">'+esc(s)+'</span>').join("");
  const skills=(o.competences||[]).slice(0,5).map(s=>'<span class="badge skill">'+esc(s)+'</span>').join("");
  const url=(o.source_ids||[]).find(x=>x.url)?.url||o.url||"";
  return '<article class="job"><div class="job-top"><div><h3>'+esc(o.titre||"Sans intitulé")+'</h3><div class="job-meta">'+esc(o.entreprise)+' · '+esc(o.ville||"Localisation non précisée")+' · '+esc(o.contrat)+'</div></div>'+(url?'<a class="external" href="'+esc(url)+'" target="_blank" rel="noopener">Voir l’offre ↗</a>':"")+'</div><div class="badges">'+sources+skills+(o.teletravail?'<span class="badge">Télétravail</span>':"")+'</div></article>'
 }).join(""):'<div class="empty">Aucune offre ne correspond à ces filtres.</div>';
}
function renderInsights(list){
 const comp={};const villes={};
 for(const o of list){for(const c of o.competences||[])comp[c]=(comp[c]||0)+1;if(o.ville)villes[o.ville]=(villes[o.ville]||0)+1}
 const topC=Object.entries(comp).sort((a,b)=>b[1]-a[1]).slice(0,10);
 if(chart)chart.destroy();
 chart=new Chart($("#chart-competences"),{type:"bar",data:{labels:topC.map(x=>x[0]),datasets:[{data:topC.map(x=>x[1]),borderWidth:0,backgroundColor:"#5b5cf0",borderRadius:5}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:"#eef0f2"},ticks:{precision:0}},y:{grid:{display:false}}}}});
 const topV=Object.entries(villes).sort((a,b)=>b[1]-a[1]).slice(0,10);
 $("#villes").innerHTML=topV.map(([v,n])=>'<div class="rank-row"><span>'+esc(v)+'</span><b>'+fmt(n)+'</b></div>').join("")||'<span class="job-meta">Pas assez de données.</span>';
}
function refresh(){const list=current();renderJobs(list);renderInsights(list)}
async function init(){
 try{
  const r=await fetch("data/multisource.json",{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);DATA=await r.json();
  $("#status-dot").classList.add("ok");$("#maj").textContent="Données du "+(DATA.date||"—");
  $("#k-offres").textContent=fmt(DATA.stats?.offres_uniques);$("#k-brut").textContent=fmt(DATA.stats?.offres_avant_dedoublonnage)+" annonces avant fusion";
  $("#k-doublons").textContent=fmt(DATA.stats?.doublons_fusionnes);$("#k-sources").textContent=fmt(DATA.stats?.sources_actives?.length);
  $("#k-source-names").textContent=(DATA.stats?.sources_actives||[]).map(x=>x.replace("_"," ")).join(" · ")||"—";
  optionList($("#source"),uniq(DATA.offres.flatMap(o=>o.sources||[o.source_label])));optionList($("#contrat"),uniq(DATA.offres.map(o=>o.contrat)));
  ["q","source","contrat","remote"].forEach(id=>$("#"+id).addEventListener(id==="q"?"input":"change",refresh));
  $("#reset").addEventListener("click",()=>{$("#q").value="";$("#source").value="";$("#contrat").value="";$("#remote").checked=false;refresh()});
  refresh();
 }catch(e){$("#maj").textContent="Données indisponibles";$("#offres").innerHTML='<div class="empty">Le fichier multisource n’a pas encore été généré. Lancez le workflow de collecte.</div>';console.error(e)}
}
init();
