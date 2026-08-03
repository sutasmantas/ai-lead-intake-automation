let state = null;
let selectedId = null;
const $ = (id) => document.getElementById(id);
const browserMode = window.location.hostname.endsWith('github.io') || new URLSearchParams(window.location.search).has('static');
let browserState = browserMode ? structuredClone(window.LEADDOCK_BROWSER_SEED) : null;

function notice(message) {
  const el = $('notice'); el.textContent = message; el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2400);
}

async function api(path, options = {}) {
  if (browserMode) return browserApi(path, options);
  const response = await fetch(path, {headers: {'Content-Type': 'application/json'}, ...options});
  const body = await response.json();
  if (!response.ok) throw new Error(body.message || body.error);
  return body;
}

function audit(event, subject, details) {
  browserState.audit.push({seq: browserState.audit.length + 1, event, subject, details});
}

function browserApi(path, options = {}) {
  const method = options.method || 'GET';
  if (path === '/api/state') return structuredClone(browserState);
  if (path === '/api/reset' && method === 'POST') {
    browserState = structuredClone(window.LEADDOCK_BROWSER_SEED);
    return {status: 'reset'};
  }
  const leadMatch = path.match(/^\/api\/leads\/([^/]+)\/(approve|reject)$/);
  if (leadMatch && method === 'POST') {
    const lead = browserState.leads.find((item) => item.id === leadMatch[1]);
    if (!lead) throw new Error('Lead not found');
    if (leadMatch[2] === 'reject') {
      lead.status = 'rejected';
      audit('lead.rejected', lead.id, {reason: 'operator decision'});
      return {status: lead.status};
    }
    const payload = JSON.parse(options.body || '{}');
    const booking = {id: `booking_${lead.id.slice(-5)}`, lead_id: lead.id, start_utc: payload.slot_start};
    lead.status = 'booked';
    lead.crm = {id: `crm_${lead.id.slice(-5)}`, status: 'upserted'};
    lead.booking = booking;
    lead.handoff = {status: lead.company === 'Retry Works' ? 'dead_letter' : 'delivered'};
    browserState.bookings.push(booking);
    browserState.availability = browserState.availability.filter((slot) => slot.start !== payload.slot_start);
    audit('crm.upserted', lead.id, {crm_id: lead.crm.id});
    audit('booking.created', lead.id, {booking_id: booking.id});
    if (lead.company === 'Retry Works') {
      browserState.dead_letters.push({id: 'dlq_retry_works', error: 'provider timeout', attempts: 3, status: 'pending'});
      audit('handoff.dead_lettered', lead.id, {attempts: 3});
    } else audit('handoff.delivered', lead.id, {status: 'delivered'});
    return structuredClone(lead);
  }
  const replayMatch = path.match(/^\/api\/dead-letters\/([^/]+)\/replay$/);
  if (replayMatch && method === 'POST') {
    const letter = browserState.dead_letters.find((item) => item.id === replayMatch[1]);
    if (!letter) throw new Error('Dead letter not found');
    letter.status = 'replayed';
    audit('handoff.replayed', letter.id, {status: 'delivered'});
    return {status: 'delivered'};
  }
  throw new Error(`Unsupported browser action: ${method} ${path}`);
}

async function refresh() {
  state = await api('/api/state');
  if (!selectedId || !state.leads.some((lead) => lead.id === selectedId)) selectedId = state.leads[0]?.id;
  render();
}

function render() { renderArrivals(); renderSelected(); renderTimeline(); renderReceipts(); renderDeadLetters(); }

function renderArrivals() {
  $('arrivals').innerHTML = state.leads.map((lead) => `
    <button class="arrival" data-id="${lead.id}" aria-pressed="${lead.id === selectedId}">
      <div class="arrival-top"><strong>${lead.company}</strong><span class="tier ${lead.qualification.tier}">${lead.qualification.tier}</span></div>
      <p>${lead.need}</p>
      <div class="arrival-meta"><span>${lead.name}</span><span>${lead.status.replaceAll('_', ' ')}</span></div>
    </button>`).join('');
  document.querySelectorAll('.arrival').forEach((button) => button.addEventListener('click', () => { selectedId = button.dataset.id; render(); }));
}

function renderSelected() {
  const lead = state.leads.find((item) => item.id === selectedId);
  if (!lead) return;
  const canBook = lead.status === 'needs_approval';
  $('selected-slip').innerHTML = `
    <small>SELECTED INTAKE SLIP</small><h3 class="slip-company">${lead.company}</h3><p class="slip-name">${lead.name} · ${lead.email}</p>
    <div class="score"><strong>${lead.qualification.score}</strong><p><b>${lead.qualification.tier.toUpperCase()}</b><br>Deterministic qualification from budget, size, need and timeline.</p></div>
    <p class="slip-need">${lead.need}</p><span class="slip-status">${lead.status.replaceAll('_', ' ')}</span>
    ${canBook ? `<label><small>OFFER VALID SLOT</small><select class="slot-picker" id="slot-picker">${state.availability.map((slot) => `<option value="${slot.start}">${slot.label}</option>`).join('')}</select></label><button class="primary" id="approve">Approve + book</button><button class="reject" id="reject">Reject lead</button>` : ''}
    ${lead.booking ? `<p class="slip-need"><b>Booking receipt</b><br>${lead.booking.id}<br>${lead.booking.start_utc}</p>` : ''}`;
  $('approve')?.addEventListener('click', async () => {
    try { await api(`/api/leads/${lead.id}/approve`, {method:'POST', body: JSON.stringify({slot_start: $('slot-picker').value})}); notice('CRM upserted, slot booked, handoff recorded.'); await refresh(); } catch (error) { notice(error.message); }
  });
  $('reject')?.addEventListener('click', async () => { await api(`/api/leads/${lead.id}/reject`, {method:'POST', body: JSON.stringify({reason:'operator decision'})}); notice('Lead rejected and audited.'); await refresh(); });
}

function renderTimeline() {
  const slots = state.availability.slice(0, 10).map((slot) => ({...slot, booking: null}));
  state.bookings.forEach((booking) => slots.push({start: booking.start_utc, label: new Date(booking.start_utc).toLocaleString([], {weekday:'short', day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'}), booking}));
  slots.sort((a,b) => a.start.localeCompare(b.start));
  $('timeline').innerHTML = slots.map((slot) => {
    const lead = slot.booking && state.leads.find((item) => item.id === slot.booking.lead_id);
    return `<div class="day"><div class="time">${slot.label.split('·').at(-1)}</div><div class="slot ${slot.booking ? 'booked' : ''}">${slot.booking ? `<span class="who">${lead.company} · ${lead.name}</span><span class="booking-id">${slot.booking.id}</span>` : `<span>available</span><span class="booking-id">30 min</span>`}</div></div>`;
  }).join('');
}

function renderReceipts() {
  $('event-count').textContent = `${state.audit.length} events`;
  $('receipts').innerHTML = [...state.audit].reverse().slice(0, 12).map((event) => `<li><b>${String(event.seq).padStart(3,'0')} · ${event.event}</b><span>${event.subject} · ${Object.values(event.details).slice(0,2).join(' · ')}</span></li>`).join('');
}

function renderDeadLetters() {
  const pending = state.dead_letters.filter((letter) => letter.status === 'pending');
  $('dead-letters').innerHTML = pending.length ? pending.map((letter) => `<div class="dead-letter"><span><b>${letter.id}</b> · ${letter.error} · ${letter.attempts} attempts</span><button class="replay" data-dlq="${letter.id}">Replay handoff</button></div>`).join('') : '<p>No unresolved handoffs.</p>';
  document.querySelectorAll('.replay').forEach((button) => button.addEventListener('click', async () => { await api(`/api/dead-letters/${button.dataset.dlq}/replay`, {method:'POST', body:'{}'}); notice('Dead letter replayed through the messaging contract.'); await refresh(); }));
}

$('reset').addEventListener('click', async () => { await api('/api/reset', {method:'POST', body:'{}'}); selectedId = null; notice('Seeded day restored.'); await refresh(); });
refresh().catch((error) => notice(error.message));
