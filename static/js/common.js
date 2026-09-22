const $=s=>document.querySelector(s);document.querySelector('#updatedAt').textContent=new Date().toLocaleString('zh-CN',{hour12:false});document.querySelector('#menuBtn').onclick=()=>document.querySelector('#sidebar').classList.toggle('open');document.addEventListener('click',e=>{if(innerWidth<=720&&!e.target.closest('#sidebar')&&!e.target.closest('#menuBtn'))document.querySelector('#sidebar').classList.remove('open')});
function toast(msg,type='ok'){const e=$('#toast');e.textContent=msg;e.className=type==='error'?'show error':'show';setTimeout(()=>e.className='',2600)}
async function getJSON(url){const r=await fetch(url),j=await r.json();if(!j.success)throw Error(j.message);return j.data}
function loadTable(url,done){getJSON(url).then(done).catch(e=>toast(e.message,'error'))}
function emptyRow(n){return `<tr><td colspan="${n}" style="text-align:center;color:#8493a7">暂无符合条件的数据</td></tr>`}
function badgeClass(s){if(['运行','已完成','正常'].includes(s))return'b-green';if(['故障','延期','已逾期','库存不足'].includes(s))return'b-red';if(['停机','未开始','待生产'].includes(s))return'';if(['库存过高','待交付'].includes(s))return'b-orange';return'b-blue'}

