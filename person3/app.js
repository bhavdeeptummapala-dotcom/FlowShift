const content = document.querySelector('#content');
const message = document.querySelector('#message');
const nav = [...document.querySelectorAll('nav button')];
const money = cents => cents == null ? 'Unavailable' : new Intl.NumberFormat('en-US', {
  style:'currency',currency:'USD'
}).format(cents/100);
const esc = value => String(value).replace(/[&<>"']/g, c => ({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c]));
const metric = (label, value) => `<div class="metric">${esc(label)}<strong>${esc(value)}</strong></div>`;
let state, result, resultVersion, page = 'Daily plan', filter = 'All', period = '2026', busy = false;
const filters = ['All','Alerts','Suggestions','Savings'];

async function api(path, data) {
  const res = await fetch('/api/'+path, data === undefined ? undefined : {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Request failed.');
  return json;
}

async function run(work) {
  if (busy) return;
  busy = true;
  content.setAttribute('aria-busy','true');
  message.textContent = '';
  try { await work(); }
  catch (error) { message.textContent = error.message; }
  finally { busy = false; content.removeAttribute('aria-busy'); }
}

function daily() {
  const d = state.dashboard;
  const items = d.feed.filter(i => filter === 'All' || i.kind === filter);
  return `<div class="card"><h2>Today’s cash position</h2>
    <p class="muted">Synthetic snapshot · ${esc(d.asOf)} · ${esc(d.plan)} · rules v${state.version}
    ${state.fresh ? '' : ' · Stale'}</p>
    <div class="metrics">${metric('Safe to Spend',money(d.safe))}${metric('Reserve target',money(d.reserve))}
    ${metric('Reserve gap',money(d.gap))}${metric('Needs action',d.count)}</div>
    <p>Based on the lowest balance checkpoint in the 14-day committed plan, less your active reserve.
    ${state.scenario === 'rescue' ? 'This plan includes simulated settled actions.' : 'The rescue suggestion is a draft and does not affect this amount.'}</p>
    <details><summary>Forecast and weekly outlook</summary>
    <p>Lowest modeled balance: ${money(d.low)}. Week-one ending balance: ${money(d.days[6].balance)}.
    This arithmetic fixture has no modeled uncertainty.</p>
    <div class="table-wrap"><table><thead><tr><th scope="col">Business date</th><th scope="col">Closing balance</th></tr></thead>
    <tbody>${d.days.map(i=>`<tr><td>${esc(i.date)}</td><td>${money(i.balance)}</td></tr>`).join('')}</tbody></table></div></details></div>
    <div class="card"><h2>Activity</h2><p class="muted">As of ${esc(d.asOf)}</p><div class="toolbar" aria-label="Activity filters">
    ${filters.map(f=>`<button data-filter="${f}" aria-pressed="${f===filter}">${f}</button>`).join('')}</div>
    ${items.map(i=>`<details class="row"><summary>${esc(i.kind)} · ${esc(i.title)}</summary><p>${esc(i.detail)}</p>
    <small>Source: ${esc(i.source)} · ${i.kind === 'Alerts' ? 'Open' : i.kind === 'Savings' ? 'Simulated' : 'Draft'}</small>
    ${i.kind==='Savings'?'<p><button data-goto="Savings receipt">Open receipt</button></p>':''}</details>`).join('') || '<p>No activity matches this filter.</p>'}</div>
    <div class="card"><h2>Demo controls</h2><p>Replay a settled rescue from the shared project fixture, or show how stale data affects the dashboard.</p>
    <div class="toolbar"><button class="primary" data-fixture="settle" ${!state.fresh || state.scenario==='rescue'?'disabled':''}>Replay settled rescue</button>
    <button data-fixture="${state.fresh?'stale':'refresh'}">${state.fresh?'Mark data stale':'Refresh fixture'}</button></div></div>`;
}

function rules() {
  const r = state.rules;
  const input = (key,label) => `<label>${label} (USD) <input name="${key}" inputmode="decimal" required pattern="[0-9]+([.][0-9]{1,2})?" value="${(r[key]/100).toFixed(2)}"></label>`;
  const check = (key,label) => `<label><input type="checkbox" name="${key}" ${r[key]?'checked':''}> ${label}</label>`;
  return `<div class="card"><h2>Rules and guardrails</h2><p>Active version ${state.version}. Saving recalculates the dashboard and clears prior preview results.</p>
    <form id="rules"><input type="hidden" name="version" value="${state.version}"><fieldset><legend>Spending limits</legend>
    ${input('reserve','Minimum cash reserve')}${input('ceiling','Per-action ceiling including fees')}${input('aggregate','Combined plan and daily ceiling')}
    ${check('instant','Use instant rails only with a documented cost advantage')}
    <p>Payroll protection and the reserve floor are enforced. New or changed payees always require human approval.</p></fieldset>
    <fieldset><legend>Notification preferences</legend>${check('routine','Send routine daily summaries')}${check('weekends','Allow weekend summaries')}
    <p>Critical payroll alerts remain available regardless of routine preferences.</p></fieldset>
    <div class="toolbar"><button class="primary">Save rules</button><button type="reset">Discard edits</button></div></form></div>`;
}

function previews() {
  return `<div class="card"><h2>Historical autopilot preview</h2><p>Replay synthetic plans against current rules using inputs available on each replay date. No actions are approved or paid.</p>
    <button class="primary" data-preview>Run historical preview</button>
    ${result && resultVersion === state.version ? `<p>${result.filter(i=>i.eligible).length} of ${result.length} plans would qualify under rules v${state.version}.</p>
    ${result.map(p=>`<details class="row"><summary>${esc(p.name)} · ${p.eligible?'Would qualify':'Blocked'}</summary>
      <p>${esc(p.asOf)} · Combined exposure ${money(p.total)}</p><ul>
      ${p.actions.map(a=>`<li>${esc(a.name)} · ${money(a.exposure)}: ${esc(a.reasons.join('; ') || (p.eligible?'Qualifies':'Passes individually; combined plan blocked'))}</li>`).join('')}</ul></details>`).join('')}` : ''}</div>`;
}

async function savings() {
  const r = await api('receipt?period='+encodeURIComponent(period));
  return `<div class="card"><h2>Savings receipt <span class="badge">Simulated</span></h2>
    <p>Compared with the documented baseline. These amounts are modeled and no money was saved or moved in a bank account.</p>
    <div class="toolbar"><label>Period <select id="period">${['2026','2026-04','2026-05','2025'].map(p=>`<option ${p===period?'selected':''}>${p}</option>`).join('')}</select></label>
    <a class="button" href="/api/receipt.csv?period=${encodeURIComponent(period)}" download>Download CSV</a></div>
    <div class="metrics">${metric('Gross benefits',money(r.gross))}${metric('Execution costs',money(r.cost))}${metric('Net modeled savings',money(r.net))}${metric('Modeled incidents avoided',r.count)}</div>
    <h3>Monthly totals</h3>${Object.entries(r.monthly).map(([m,n])=>`<p>${esc(m)} · ${money(n)}</p>`).join('') || '<p>No simulated entries in this period.</p>'}
    <h3>Category and evidence</h3>${r.rows.map(i=>`<details class="row"><summary>${esc(i.category)} · ${money(i.gross-i.cost)} net</summary>
      <p>${esc(i.date)} · ${esc(i.baseline)}</p><p>${esc(i.action)}</p><small>${esc(i.id)} · Simulated</small></details>`).join('') || '<p>Nothing to attribute for this period.</p>'}</div>`;
}

function notifications() {
  return `<div class="card"><h2>Notification simulator</h2><p>Advance the synthetic clock to check the 7 a.m. Central summary and critical payroll reminders. No messages leave this workspace.</p>
    <form id="notices"><label>Business time <input type="datetime-local" name="at" required value="2026-04-20T09:00"></label>
    <button class="primary">Run notification check</button></form>
    ${state.notices.map(i=>`<details class="row"><summary>${esc(i.title)} · ${esc(i.at)}</summary><p>${esc(i.detail)}</p>
    <p>Lock-screen preview: ${esc(i.lockScreen)}</p></details>`).join('') || '<p>No notifications simulated yet.</p>'}</div>`;
}

function history() {
  return `<div class="card"><h2>Audit history</h2><p>Latest first. Entries link fixture snapshots, plan versions, and results.</p>
    ${[...state.audit].reverse().map(i=>`<details class="row"><summary>#${i.id} · ${esc(i.event)}</summary><p>${esc(i.detail)}</p>
    <small>${esc(i.at)} · ${esc(i.actor)} · ${esc(i.mode)} · rules v${i.rulesVersion}</small></details>`).join('')}</div>`;
}

async function render() {
  nav.forEach(b=> b.dataset.page===page ? b.setAttribute('aria-current','page') : b.removeAttribute('aria-current'));
  const views = {'Daily plan':daily,'Rules':rules,'Autopilot preview':previews,
    'Savings receipt':savings,'Notifications':notifications,'Audit history':history};
  content.innerHTML = await views[page]();
}

document.querySelector('nav').addEventListener('click',e=>{
  const next = e.target.dataset.page;
  if (next) run(async()=>{page=next; state=await api('state'); await render();});
});

content.addEventListener('click',e=>{
  const b=e.target.closest('button');
  if (!b || b.type==='reset') return;
  if (b.dataset.filter) run(async()=>{filter=b.dataset.filter; await render();
    [...content.querySelectorAll('[data-filter]')].find(i=>i.dataset.filter===filter)?.focus();});
  if (b.dataset.goto) run(async()=>{page=b.dataset.goto; await render(); nav.find(i=>i.dataset.page===page)?.focus();});
  if (b.dataset.fixture) run(async()=>{state=await api('fixture',{action:b.dataset.fixture}); await render(); message.textContent='Demo state updated.';});
  if ('preview' in b.dataset) run(async()=>{state=await api('preview',{}); result=state.preview; resultVersion=state.version; await render(); message.textContent='Historical preview ready.';});
});

content.addEventListener('change',e=>{
  if (e.target.id==='period') run(async()=>{period=e.target.value; await render(); content.querySelector('#period').focus();});
});

content.addEventListener('submit',e=>{
  e.preventDefault();
  const f = new FormData(e.target);
  run(async()=>{
    if (e.target.id==='rules') {
      const r={};
      for (const key of ['reserve','ceiling','aggregate']) {
        const [whole,fraction=''] = f.get(key).split('.');
        r[key] = Number(whole)*100+Number(fraction.padEnd(2,'0'));
      }
      for (const key of ['instant','routine','weekends']) r[key]=f.has(key);
      state=await api('rules',{version:Number(f.get('version')),rules:r});
      result=null;
      message.textContent='Rules saved.';
    } else {
      state=await api('notices',{at:f.get('at')});
      message.textContent='Notification check complete. Duplicate events are suppressed.';
    }
    await render();
    if (e.target.id==='notices') content.querySelector('[name="at"]').value=f.get('at');
  });
});

run(async()=>{state=await api('state'); await render();});
