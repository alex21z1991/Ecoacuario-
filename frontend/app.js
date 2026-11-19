const API = ""; // Mismo origen: Flask sirve la web y la API.
const $ = (id) => document.getElementById(id);
let chart = null;
let currentStatus = null;
let refreshTimer = null;

async function api(path, options={}) {
  const response = await fetch(`${API}/api${path}`, {
    headers: {"Content-Type":"application/json", ...(options.headers||{})},
    ...options
  });
  const data = await response.json().catch(()=>({message:"Respuesta no válida del servidor"}));
  if (!response.ok) throw new Error(data.message || data.error || `Error HTTP ${response.status}`);
  return data;
}
function toast(message) {
  const el=$("toast"); el.textContent=message; el.classList.add("show");
  setTimeout(()=>el.classList.remove("show"),2600);
}
function fmtTime(value) {
  if(!value) return "--";
  return new Date(value).toLocaleString("es-CL",{hour:"2-digit",minute:"2-digit",day:"2-digit",month:"2-digit"});
}
function setBadge(id, reading, lowText="En intervalo") {
  const el=$(id);
  if(!reading){el.textContent="Sin dato";el.className="pill neutral";return}
  if(!reading.valid){el.textContent=reading.expired?"Vencido":"Inválido";el.className="pill bad"}
  else {el.textContent=lowText;el.className="pill"}
}
function setOutput(id, on, blocked=false) {
  const el=$(id); el.textContent=on?"Encendida":"Apagada";
  el.className="state "+(blocked?"blocked":on?"on":"off");
}
function renderStatus(data) {
  currentStatus=data;
  const r=data.readings||{}, c=data.config||{};
  $("phValue").textContent=r.ph?.value!=null?Number(r.ph.value).toFixed(1):"--";
  $("tempValue").textContent=r.temperature?.value!=null?`${Number(r.temperature.value).toFixed(1)} °C`:"--";
  $("levelValue").textContent=r.level?.value!=null?`${Number(r.level.value).toFixed(1)} cm`:"--";
  setBadge("phBadge",r.ph); setBadge("tempBadge",r.temperature); setBadge("levelBadge",r.level);
  $("phMeta").textContent=r.ph?`Límites de prueba: ${c.ph_min}–${c.ph_max} · ${fmtTime(r.ph.timestamp)}`:"Esperando lectura";
  $("tempMeta").textContent=r.temperature?`Límites alerta: ${c.temp_min}–${c.temp_max} °C · ${fmtTime(r.temperature.timestamp)}`:"Esperando lectura";
  $("levelMeta").textContent=r.level?`Altura desde el fondo · ${fmtTime(r.level.timestamp)}`:"Esperando lectura";
  $("lastUpdate").textContent=`Servidor: ${fmtTime(data.server_time)}`;
  const blocked=!!data.blocked;
  $("globalWarning").classList.toggle("hidden",!blocked);
  $("globalWarning").textContent=blocked?"Nivel bajo, inválido o vencido: las salidas afectadas permanecen bloqueadas.":"Condiciones de nivel sin bloqueo.";
  const o=data.outputs||{};
  setOutput("pumpState",o.pump,blocked); setOutput("heaterState",o.heater,blocked);
  setOutput("pumpControlState",o.pump,blocked); setOutput("heaterControlState",o.heater,blocked);
  $("pumpReason").textContent=blocked?"Bloqueada por condición de nivel":"Funcionamiento tras confirmación";
  $("heaterReason").textContent=`Modo ${o.heater_mode==="automatic"?"automático":"manual"}`;
  $("pumpControlReason").textContent=blocked?"Revisar nivel; el encendido está bloqueado.":(o.pump_needs_confirmation?"Confirmar Encender para reanudar la bomba.":"La bomba está habilitada mientras el nivel sea válido.");
  $("heaterControlReason").textContent=blocked?"Encendido bloqueado por nivel.":`Modo ${o.heater_mode==="automatic"?"Automático":"Manual"}; consignas ${c.heater_on} °C / ${c.heater_off} °C.`;
  $("heaterMode").value=o.heater_mode||"automatic";
  $("controlWarning").classList.toggle("hidden",!blocked);
  $("controlWarning").textContent=blocked?"Bloqueo de seguridad activo: la bomba y el calefactor no pueden encenderse.":"No hay bloqueo de nivel activo.";
  $("connectionDot").className="dot online"; $("connectionText").textContent="Servidor conectado";
  $("modeTag").textContent="MODO DEMOSTRACIÓN";
}
async function loadStatus(){try{renderStatus(await api("/status"))}catch(e){$("connectionDot").className="dot offline";$("connectionText").textContent="Sin conexión con el servidor";$("globalWarning").classList.remove("hidden");$("globalWarning").textContent="No se pudo consultar la Raspberry Pi. Comprueba la conexión Wi-Fi y el servidor.";}}
async function loadHistory(){
  const variable=$("historyVariable").value;
  try{
    const data=await api(`/history?variable=${variable}&hours=24`);
    const records=data.records||[];
    $("historyRows").innerHTML=records.slice().reverse().map(x=>`<tr><td>${fmtTime(x.timestamp)}</td><td>${x.value==null?"--":x.value}</td><td>${x.valid?"Válido":`Inválido · ${x.reason||"sin detalle"}`}</td></tr>`).join("")||'<tr><td colspan="3">No hay registros para este período.</td></tr>';
    const labels=records.map(x=>new Date(x.timestamp).toLocaleTimeString("es-CL",{hour:"2-digit",minute:"2-digit"}));
    const values=records.map(x=>x.valid?x.value:null);
    const ctx=$("historyChart");
    if(chart)chart.destroy();
    chart=new Chart(ctx,{type:"line",data:{labels,datasets:[{label:variable==="temperature"?"Temperatura":variable==="ph"?"pH":"Nivel",data:values,borderColor:"#009b89",backgroundColor:"rgba(0,155,137,.10)",borderWidth:2,tension:.25,spanGaps:false,pointRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:false},x:{ticks:{maxTicksLimit:6}}}}});
  }catch(e){toast(e.message)}
}
async function loadConfig(){
  try{const c=await api("/config");Object.entries(c).forEach(([k,v])=>{const input=document.querySelector(`[name="${k}"]`);if(input)input.value=v})}catch(e){toast(e.message)}
}
async function loadAlerts(){
  try{
    const data=await api("/alerts");
    const active=(data.alerts||[]).filter(a=>a.active);
    const closed=(data.alerts||[]).filter(a=>!a.active && !a.kind.startsWith("control_")).slice(0,5);
    const items=[...active,...closed];
    $("alertsList").innerHTML=items.map(a=>`<article class="alert-card ${a.active?"":"closed"}"><h3>${a.active?"● Activa":"✓ Evento / cerrada"} · ${escapeHtml(a.message)}</h3><p>${escapeHtml(a.recommendation||"Registro de evento del sistema.")}</p><p class="alert-time">${fmtTime(a.timestamp)}</p></article>`).join("")||'<article class="panel">No hay alertas registradas.</article>';
  }catch(e){toast(e.message)}
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function showPage(page){
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  $(`page-${page}`).classList.add("active");
  document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.page===page));
  if(page==="status")loadStatus();
  if(page==="history")loadHistory();
  if(page==="limits")loadConfig();
  if(page==="alerts")loadAlerts();
  if(page==="control")loadStatus();
}
document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>showPage(b.dataset.page)));
$("historyVariable").addEventListener("change",loadHistory);
$("measureBtn").addEventListener("click",async()=>{
  $("measureBtn").disabled=true;$("measureMessage").textContent="Solicitando lectura...";
  try{const d=await api("/measure",{method:"POST"});$("measureMessage").textContent=d.message;renderStatus(d.status);toast(d.message)}
  catch(e){$("measureMessage").textContent=e.message;toast(e.message)}
  finally{$("measureBtn").disabled=false}
});
$("configForm").addEventListener("submit",async e=>{
  e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());
  Object.keys(data).forEach(k=>data[k]=Number(data[k]));
  try{const d=await api("/config",{method:"PUT",body:JSON.stringify(data)});$("configMessage").textContent=d.message;toast(d.message);await loadStatus()}
  catch(err){$("configMessage").textContent=err.message;toast(err.message)}
});
async function control(path,body){
  try{const d=await api(path,{method:"POST",body:JSON.stringify(body)});toast(d.message);if(d.status)renderStatus(d.status);await loadAlerts()}
  catch(e){toast(e.message);await loadStatus()}
}
$("pumpOn").addEventListener("click",()=>control("/control/pump",{action:"on"}));
$("pumpOff").addEventListener("click",()=>control("/control/pump",{action:"off"}));
$("heaterOn").addEventListener("click",()=>control("/control/heater",{mode:"manual",action:"on"}));
$("heaterOff").addEventListener("click",()=>control("/control/heater",{mode:"manual",action:"off"}));
$("heaterMode").addEventListener("change",e=>{
  if(e.target.value==="automatic")control("/control/heater",{mode:"automatic",action:"auto"});
  else control("/control/heater",{mode:"manual",action:"off"});
});
loadStatus();loadConfig();
refreshTimer=setInterval(()=>{loadStatus();if($("page-history").classList.contains("active"))loadHistory();if($("page-alerts").classList.contains("active"))loadAlerts()},15000);
