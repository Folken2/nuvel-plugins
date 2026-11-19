/* Chief of Staff dashboard: the live board. Reads the registry through the viewer's own
 * connectors and writes only what the viewer clicks: close handoffs in the registry,
 * Gmail drafts (never sent) and busy calendar blocks (nobody invited).
 * Contract: references/dashboard.md. Settings come from build_dashboard.py. */
(function () {
"use strict";
var CFG = JSON.parse(document.getElementById("cos-settings").textContent);
var R = window.CosRadar, STR = window.COS_STRINGS;
var LANG = STR.S[CFG.owner.language] ? CFG.owner.language : "en";
var LOC = { en: "en-GB", ca: "ca", es: "es" }[LANG];
var TZ = CFG.owner.timezone || undefined;
var SRV = { drive: "Google Drive", mail: "Gmail", cal: "Google Calendar" };
var PROV = { mail: "Gmail", cal: "Google Calendar", conn: "Google Drive", name: "Google",
  calUrl: "https://calendar.google.com/calendar/r/day" };

function t(k, v) { var s = STR.S[LANG][k] || STR.S.en[k] || k; if (v) for (var x in v) s = s.split("{" + x + "}").join(v[x]); return s; }

/* ---------- per-viewer memory (never shared, never read by Claude) ---------- */
var KEY = "cos.dash." + CFG.storage.root;
var MEM = { doing: {}, closing: {}, read: {}, side: false, theme: "auto", answered: {} };
try { var m0 = JSON.parse(localStorage.getItem(KEY) || "{}"); for (var k0 in MEM) if (m0[k0] != null) MEM[k0] = m0[k0]; } catch (e) {}
function save() { try { localStorage.setItem(KEY, JSON.stringify(MEM)); } catch (e) {} }

/* ---------- time in the owner's timezone ---------- */
function parts(d) {
  var o = {}; new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).forEach(function (p) { o[p.type] = p.value; });
  return { date: o.year + "-" + o.month + "-" + o.day, hm: o.hour + ":" + o.minute };
}
function today() { return parts(new Date()).date; }
function addDays(s, n) { var x = new Date(s + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); }
function dd(a, b) { return Math.round((new Date(b + "T12:00:00Z") - new Date(a + "T12:00:00Z")) / 864e5); }
function fmt(s, o) { return new Date(s + "T12:00:00Z").toLocaleDateString(LOC, Object.assign({ timeZone: "UTC" }, o)); }
function wk(s) { return fmt(s, { weekday: "short" }); }
function dlong(s) { return fmt(s, { weekday: "short", day: "numeric", month: "short" }); }
function rel(s) { var n = dd(s, today()); return n === 0 ? t("today") : n === 1 ? t("yesterday") : dlong(s); }
function mm(s) { return +s.slice(0, 2) * 60 + +s.slice(3, 5); }
function hhmm(n) { return String(Math.floor(n / 60)).padStart(2, "0") + ":" + String(n % 60).padStart(2, "0"); }
function hours() {
  var m = /(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})/.exec(CFG.owner.working_hours || "");
  return m ? [mm(m[1].padStart(5, "0")), mm(m[2].padStart(5, "0"))] : [540, 1140];
}

/* ---------- state ---------- */
var mcp = null, booted = false;
var ST = { phase: "loading", model: null, radar: null, brief: null, meetings: [], free: [], prepared: {}, proposals: [],
  err: { drive: null, cal: null }, canDraft: false, canEvent: false, calOn: CFG.calendar === "google" };
var timers = {};

function errText(e, server) {
  var c = e && e.code || "upstream_error", k = "e_" + c;
  var s = STR.S[LANG][k] || STR.S.en[k] ? t(k, { s: server }) : t("e_other", { s: server, c: c });
  return s;
}

/* ---------- connector calls ---------- */
function call(server, tool, input, fresh) {
  return mcp.callTool(server, tool, input, fresh ? { cache: { refresh: true, staleTime: 0, gcTime: 300000 } } : undefined)
    .then(function (r) { return r.payload || {}; });
}
function q(s) { return "'" + String(s).replace(/\\/g, "\\\\").replace(/'/g, "\\'") + "'"; }
function isoAgo(days) { return new Date(Date.now() - days * 864e5).toISOString().replace(/\.\d+Z$/, "Z"); }

function findDocs(fresh) {
  var base = "parentId = " + q(CFG.storage.runs) + " and (title contains 'radar' or title contains 'brief' or title contains 'prepared')";
  function search(days) {
    var query = days ? base + " and createdTime > " + q(isoAgo(days)) : base;
    return call(SRV.drive, "search_files", { query: query, excludeContentSnippets: true, pageSize: 100 }, fresh)
      .then(function (p) { return p.files || []; });
  }
  return search(3).then(function (f) { return R.newest(f, "radar") ? f : search(14); })
    .then(function (f) { return R.newest(f, "radar") ? f : search(0); });
}

function readDoc(id, fresh) { return call(SRV.drive, "read_file_content", { fileId: id }, fresh).then(function (p) { return p.fileContent || ""; }); }

function loadCalendar(fresh) {
  if (!ST.calOn) return Promise.resolve();
  var d = today();
  return call(SRV.cal, "list_events", { startTime: d + "T00:00:00", endTime: d + "T23:59:59", timeZone: TZ,
    orderBy: "startTime", pageSize: 50 }, fresh).then(function (p) {
    ST.err.cal = null;
    ST.meetings = (p.events || []).filter(function (e) {
      if (!e.start || !e.start.dateTime || e.status === "cancelled") return false;
      var me = (e.attendees || []).filter(function (a) { return a.self; })[0];
      return !(me && me.responseStatus === "declined");
    }).map(function (e) {
      var a = parts(new Date(e.start.dateTime)), b = parts(new Date(e.end.dateTime));
      return { t: a.hm, e: b.date > d ? "23:59" : b.hm, title: e.summary || "", sub: e.conferenceUrl ? "Google Meet" : (e.location || ""),
        link: e.htmlLink || null };
    });
  }).catch(function (e) { ST.err.cal = e; ST.meetings = []; });
}

function loadProposals(fresh) {  // suggested rules from the user's decisions, waiting for a yes or no
  if (!CFG.storage.lessons) return Promise.resolve();
  return call(SRV.drive, "search_files", { query: "parentId = " + q(CFG.storage.lessons) + " and title contains 'lessons'",
    excludeContentSnippets: true, pageSize: 50 }, fresh).then(function (p) {
    var f = R.newestLessons(p.files || []); if (!f) { ST.proposals = []; return; }
    return readDoc(f.id, fresh).then(function (txt) { ST.proposals = R.parseLessons(txt).proposed; });
  }).catch(function () { ST.proposals = []; });
}
function freeBlocks() {
  var wh = hours(), busy = ST.meetings.map(function (m) { return [mm(m.t), mm(m.e)]; }).sort(function (a, b) { return a[0] - b[0]; });
  var out = [], cur = wh[0];
  busy.forEach(function (b) { if (b[0] - cur >= 45 && cur < wh[1]) out.push([cur, Math.min(b[0], wh[1])]); cur = Math.max(cur, b[1]); });
  if (wh[1] - cur >= 45) out.push([cur, wh[1]]);
  var sug = (ST.brief && ST.brief.free) || [];
  return out.map(function (f) {
    var s = sug.filter(function (x) { return mm(x.from) < f[1] && mm(x.to) > f[0]; })[0];
    return { t: hhmm(f[0]), e: hhmm(f[1]), use: s ? s.use : "" };
  });
}

function load(fresh) {
  if (CFG.storage.kind !== "google-drive") { ST.phase = "ms"; render(); return Promise.resolve(); }
  var boot = booted ? Promise.resolve(mcp) : (window.claude && window.claude.use ? window.claude.use("mcp") : Promise.resolve(null));
  return boot.then(function (m) {
    booted = true; mcp = m;
    if (!mcp) { ST.phase = "nomcp"; render(); return; }
    return mcp.listTools().then(function (lt) {
      var has = {}; (lt.servers || []).forEach(function (s) { (s.tools || []).forEach(function (x) { has[s.server + "/" + x.name] = 1; }); });
      ST.canDraft = CFG.email === "gmail" && !!has[SRV.mail + "/create_draft"];
      ST.canEvent = ST.calOn && !!has[SRV.cal + "/create_event"];
    }).catch(function () {}).then(function () {
      return Promise.all([
        findDocs(fresh).then(function (files) {
          ST.err.drive = null;
          var radar = R.newest(files, "radar"), brief = R.newest(files, "brief");
          ST.prepared = R.preparedByTask(files);
          if (!radar) { ST.phase = "first"; ST.model = null; return; }
          var jobs = [readDoc(radar.id, fresh).then(function (txt) { ST.model = R.parseRadar(txt); ST.radar = radar; })];
          var bt = brief && R.titleTime(brief.title);
          if (bt && bt.slice(0, 10) === today()) jobs.push(readDoc(brief.id, fresh).then(function (txt) { ST.brief = R.parseBrief(txt); }).catch(function () {}));
          else ST.brief = null;
          return Promise.all(jobs).then(function () { ST.phase = "ready"; });
        }).catch(function (e) { ST.err.drive = e; if (!ST.model) ST.phase = "disc"; }),
        loadCalendar(fresh),
        loadProposals(fresh)
      ]);
    }).then(function () { ST.free = freeBlocks(); reconcile(); render(); resumeCloses(); });
  });
}

/* ---------- closing tasks: a handoff per task, after an undo window ---------- */
function openIds() {
  var ids = {}; if (!ST.model) return ids;
  ST.model.todo.concat(ST.model.dele).forEach(function (x) { if (x.id) ids[x.id] = 1; });
  return ids;
}
function reconcile() {  // the radar closed it (or it left the lists): forget our local note
  if (!ST.model) return;
  var open = openIds();
  var marked = {}; ST.model.todo.concat(ST.model.dele).forEach(function (x) { if (x.id && x.looksDone) marked[x.id] = 1; });
  for (var id in MEM.closing) {
    var c = MEM.closing[id];
    var sn = /^snooze until (\S+)/.exec(c.reason || "");
    if (c.written && (!open[id] || (c.reason === "keep open" && !marked[id]) || (sn && sn[1] <= today()))) delete MEM.closing[id];
  }
  for (var k in MEM.doing) if (!open[k]) delete MEM.doing[k];
  save();
}
var usedNames = {};  // names this page already wrote: Drive search can lag right after a write
function stamp(d) {
  var p = parts(d); return { name: p.date + " " + p.hm.replace(":", "") + " handoff", human: p.date + " " + p.hm };
}
var resumed = [], resumedTimer = null;
function announceResumed(id) {  // a close from an earlier visit reached the registry: say so, never silently
  resumed.push(id); clearTimeout(resumedTimer);
  resumedTimer = setTimeout(function () {
    var ids = resumed.slice(); resumed = [];
    if (ids.length === 1) {
      var x = todoAll().concat(ST.model ? ST.model.dele : []).filter(function (y) { return y.id === ids[0]; })[0];
      toast(t("resumedOne", { id: ids[0], title: x ? x.title : "" }).replace(/\s+\./, "."));
    } else toast(t("resumedMany", { n: ids.length, ids: ids.join(", ") }));
  }, 400);
}
function writeNote(kind, fields) {  // one handoff, written now (lesson answers, notes for learn)
  var d = new Date(), tries = 0;
  function attempt() {
    var s = stamp(d);
    return call(SRV.drive, "search_files", { query: "parentId = " + q(CFG.storage.handoff) + " and title = " + q(s.name),
      excludeContentSnippets: true, pageSize: 5 }, true).then(function (p) {
      if (((p.files || []).length || usedNames[s.name]) && tries++ < 10) { d = new Date(d.getTime() + 60000); return attempt(); }
      usedNames[s.name] = 1;
      return call(SRV.drive, "create_file", { title: s.name, parentId: CFG.storage.handoff, textContent: R.note(kind, fields, s.human),
        contentMimeType: "text/markdown" });
    });
  }
  return attempt();
}
function answerProposal(pr, keep) {
  MEM.answered[pr.id] = keep ? "keep" : "drop"; save(); render();
  writeNote("lesson — " + (keep ? "keep " : "drop ") + pr.id, {}).then(function () { toast(t(keep ? "ruleKept" : "ruleDismissed")); })
    .catch(function (e) { delete MEM.answered[pr.id]; save(); render(); toast(t("closeFailed", { e: errText(e, SRV.drive) })); });
}
function writeClose(id, fromEarlier) {
  var c = MEM.closing[id]; if (!c || c.written || c.inflight || !mcp) return;
  c.inflight = true; save();
  var d = new Date(), tries = 0;
  function attempt() {
    var s = stamp(d);
    return call(SRV.drive, "search_files", { query: "parentId = " + q(CFG.storage.handoff) + " and title = " + q(s.name),
      excludeContentSnippets: true, pageSize: 5 }, true).then(function (p) {
      if (((p.files || []).length || usedNames[s.name]) && tries++ < 10) { d = new Date(d.getTime() + 60000); return attempt(); }
      usedNames[s.name] = 1;
      return call(SRV.drive, "create_file", { title: s.name, parentId: CFG.storage.handoff, textContent: R.handoff(id, c.reason, s.human),
        contentMimeType: "text/markdown" });
    });
  }
  attempt().then(function () { c.written = true; c.inflight = false; save(); render(); if (fromEarlier) announceResumed(id); })
    .catch(function (e) {
      var ambiguous = e && (e.code === "server_unavailable" || e.code === "upstream_error" || e.code === "cancelled");
      if (ambiguous) { c.inflight = false; c.check = true; save(); }  // may exist: look before writing again
      else { delete MEM.closing[id]; save(); }
      toast(t("closeFailed", { e: errText(e, SRV.drive) })); render();
    });
}
function resumeCloses() {  // a close that never reached the registry (page closed during undo, or an unclear failure)
  Object.keys(MEM.closing).forEach(function (id) {
    var c = MEM.closing[id]; if (c.written) return;
    if (!c.check && !c.inflight) { if (Date.now() - c.at > 6000) writeClose(id, true); return; }
    call(SRV.drive, "search_files", { query: "parentId = " + q(CFG.storage.handoff) + " and fullText contains " + q("task: " + id) +
      " and createdTime > " + q(new Date(c.at - 120000).toISOString().replace(/\.\d+Z$/, "Z")), excludeContentSnippets: true, pageSize: 5 }, true)
      .then(function (p) { if ((p.files || []).length) { c.written = true; c.inflight = false; c.check = false; save(); render(); announceResumed(id); }
        else { c.inflight = false; c.check = false; save(); writeClose(id, true); } }).catch(function () {});
  });
}
function requestClose(x, reason) {
  if (!x.id) { toast(t("noId")); return; }
  var c = MEM.closing[x.id];
  if (c && c.written) { toast(t("alreadySent")); return; }
  MEM.closing[x.id] = { reason: reason, at: Date.now(), written: false };
  delete MEM.doing[x.key]; save(); closeSheet(); render();
  clearTimeout(timers[x.id]);
  timers[x.id] = setTimeout(function () { writeClose(x.id); }, 6000);
  var sm = /^snooze until (\S+)/.exec(reason);
  toast(sm ? t("markedSnoozed", { d: dlong(sm[1]) }) : t(reason === "done" ? "markedDone" : reason === "keep open" ? "markedKept" : "markedNotMine"), { label: t("undo"), fn: function () {
    clearTimeout(timers[x.id]); var cc = MEM.closing[x.id];
    if (cc && (cc.written || cc.inflight)) { toast(t("alreadySent")); return; }
    delete MEM.closing[x.id]; save(); render(); toast(t("undone")); } });
}

/* ---------- model helpers ---------- */
function closing(x) { var c = x.id && MEM.closing[x.id]; return c && c.reason !== "keep open" && !/^snooze/.test(c.reason) ? c : null; }
function snoozed(x) {  // until this date the task stays out of the lists
  var c = x.id && MEM.closing[x.id], local = c && /^snooze until (\S+)/.exec(c.reason);
  var until = local ? local[1] : x.snoozedUntil;
  return until && until > today() && x.closedOn === undefined ? until : null;
}
function pending(x) { var c = closing(x); return !!(c && !c.written); }
function looksDone(x) {  // the radar thinks it's finished; only the user closes it
  var c = x.id && MEM.closing[x.id];
  return x.looksDone && x.closedOn === undefined && !(c && c.reason === "keep open") && !closing(x) ? x.looksDone : null;
}
function prepared(x) { return x.id && ST.prepared[x.id] && x.closedOn === undefined && !closing(x) ? ST.prepared[x.id] : null; }
function status(x) {
  if (x.closedOn !== undefined) return "done";
  if (closing(x)) return "done";
  return MEM.doing[x.key] ? "doing" : "todo";
}
function todoAll() { return ST.model ? ST.model.todo : []; }
function openTodo() { return todoAll().filter(function (x) { return status(x) !== "done" && !snoozed(x); }); }
function snoozedAll() { return todoAll().concat(ST.model ? ST.model.dele : []).filter(function (x) { return status(x) !== "done" && snoozed(x); }); }
function doneTodo() {
  var local = todoAll().filter(function (x) { return status(x) === "done"; });
  var closed = ST.model ? ST.model.closed.filter(function (c) { return !c.closedOn || dd(c.closedOn, today()) <= 7; }) : [];
  return local.concat(closed);
}
function openDele() { return ST.model ? ST.model.dele.filter(function (x) { return status(x) !== "done" && !snoozed(x); }) : []; }
function waited(x) { return x.since ? dd(x.since, today()) : 0; }
function overdueDele() { return openDele().filter(function (x) { return (x.due && dd(today(), x.due) < 0) || waited(x) >= 7; }); }
function infoLeft() { return ST.model ? ST.model.info.filter(function (i) { return !MEM.read[i.key]; }) : []; }
function rankTodo(list) {
  var ko = { needs: 0, decide: 1, owe: 2 };
  function band(x) { if (x.due && dd(today(), x.due) < 0) return 0; if (x.due && dd(today(), x.due) === 0) return 1; return 2 + ko[x.kind]; }
  return list.slice().sort(function (a, b) { return band(a) - band(b) || ((a.due || "9") < (b.due || "9") ? -1 : (a.due || "9") > (b.due || "9") ? 1 : 0); });
}
function hasData() { return !!ST.model && (ST.phase === "ready" || ST.phase === "disc"); }
function radarDate() { return ST.model && ST.model.at ? ST.model.at.slice(0, 10) : null; }
function stale() { var d = radarDate(); return !!d && dd(d, today()) >= 1 && ST.radar && (Date.now() - Date.parse(ST.model.at + ":00")) > 18 * 36e5; }

/* ---------- DOM helpers ---------- */
function h(tag, a) {
  var el = document.createElement(tag); a = a || {};
  for (var k in a) { var v = a[k]; if (v == null || v === false) continue;
    if (k === "class") el.className = v; else if (k === "text") el.textContent = v;
    else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v); else el.setAttribute(k, v === true ? "" : v); }
  for (var i = 2; i < arguments.length; i++) { var c = arguments[i]; if (c == null || c === false) continue;
    if (Array.isArray(c)) c.forEach(function (x) { if (x != null && x !== false) el.append(x); }); else el.append(c); }
  return el;
}
function svg(path) { var s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("aria-hidden", "true"); s.innerHTML = path; return s; }
var ICON = { today: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  todo: '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="M8 12.5l2.7 2.7L16 9.8"/>',
  dele: '<circle cx="9" cy="8" r="3.2"/><path d="M3 19c.6-3.3 3-5 6-5s5.4 1.7 6 5"/><path d="M16 4.8a3.2 3.2 0 010 6.4M18 14.3c1.7.6 2.8 2.1 3.1 4.7"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.1"/>', ext: '<path d="M7 17L17 7M9 7h8v8"/>' };
function safeUrl(u) { return /^https:\/\//i.test(u || "") ? u : null; }
function openUrl(u) { var s = safeUrl(u); if (s) window.open(s, "_blank", "noopener"); }
function initials(n) { return String(n || "").split(/\s+/).filter(Boolean).slice(0, 2).map(function (w) { return w[0]; }).join("").toUpperCase() || "·"; }
function signal(x, dele) {
  if (looksDone(x)) return h("span", { class: "sig amber", text: t("looksDoneQ") });
  if (status(x) === "done") return pending(x) ? h("span", { class: "sig amber", text: t("closing") + "…" }) : h("span", { class: "sig", text: t("st_done") });
  if (x.due) { var n = dd(today(), x.due); if (n < 0) return h("span", { class: "sig red", text: t("overdue", { n: -n }) });
    if (n === 0) return h("span", { class: "sig amber", text: t("dueToday") }); return h("span", { class: "sig", text: t("due", { d: n < 7 ? wk(x.due) : dlong(x.due) }) }); }
  if (dele && x.since) { var w = waited(x); return h("span", { class: "sig" + (w >= 7 ? " red" : ""), text: t("waiting", { n: w }) }); }
  return null;
}
function stLabel(set, s) { return s === "todo" && set === "dele" ? t("st_wait") : t("st_" + s); }

/* ---------- status ring ---------- */
function stc(x, set) {
  var s = status(x);
  return h("button", { class: "stc " + s, type: "button", "aria-label": stLabel(set, s), onclick: function (e) {
    e.stopPropagation(); setStatus(x, { todo: "doing", doing: "done", done: "todo" }[s], set); } }, h("span", { class: "ring" }));
}
function setStatus(x, s, set) {
  if (x.closedOn !== undefined) return;  // closed by the radar
  if (s === "done") { requestClose(x, "done"); return; }
  if (x.id && MEM.closing[x.id]) {
    var c = MEM.closing[x.id];
    if (c.written || c.inflight) { toast(t("alreadySent")); return; }
    clearTimeout(timers[x.id]); delete MEM.closing[x.id];
  }
  if (s === "doing") MEM.doing[x.key] = 1; else delete MEM.doing[x.key];
  save(); render(); if (sheetOpen && sheetOpen.x === x) openSheet(x, set);
  toast(t("moved", { s: stLabel(set, s) }));
}

/* ---------- navigation ---------- */
var VIEWS = ["today", "todo", "delegated", "fyi"], ICK = { today: "today", todo: "todo", delegated: "dele", fyi: "info" };
var cur = "today", todoFilter = "open";
function go(v) { if (VIEWS.indexOf(v) < 0) v = "today"; cur = v; try { if (location.hash !== "#" + v) history.replaceState(null, "", "#" + v); } catch (e) {} closeSheet(); render(); document.getElementById("main").scrollTop = 0; }
function renderNav() {
  var sn = document.getElementById("sidenav"), tb = document.getElementById("tabs"); sn.replaceChildren(); tb.replaceChildren();
  var c = { todo: openTodo().length, delegated: overdueDele().length, fyi: infoLeft().length,
    today: openTodo().filter(function (x) { return x.due && dd(today(), x.due) <= 0; }).length };
  VIEWS.forEach(function (v) {
    var n = v === "today" ? 0 : c[v];
    sn.append(h("button", { class: "nav", type: "button", title: t(v), "aria-current": cur === v ? "page" : null, onclick: function () { go(v); } },
      svg(ICON[ICK[v]]), h("span", { class: "lb", text: t(v) }), n ? h("span", { class: "c" + (v === "delegated" ? " hot" : ""), text: String(n) }) : null));
    var badge = v === "today" ? c.today : v === "delegated" ? c.delegated : 0;
    tb.append(h("button", { type: "button", role: "tab", "aria-current": cur === v ? "page" : null, onclick: function () { go(v); } },
      svg(ICON[ICK[v]]), v === "fyi" ? t("fyiShort") : t(v), badge ? h("span", { class: "dot", text: String(badge) }) : null));
  });
  var up = document.getElementById("updated"); up.className = "";
  if (ST.phase === "loading") up.textContent = t("loading");
  else if (ST.model && ST.model.at) { if (stale()) { up.className = "stale"; up.textContent = t("lastRadar", { w: dlong(radarDate()) }); }
    else up.textContent = t("updated", { t: ST.model.at.slice(11, 16) }); }
  else up.textContent = "";
  document.getElementById("refresh").textContent = t("refresh");
}

/* ---------- shared pieces ---------- */
function notice(kind, title, body, btn) {
  return h("div", { class: "notice " + kind, role: kind === "red" ? "alert" : "status" }, h("span", { class: "ic", "aria-hidden": "true", text: kind === "calm" ? "i" : "!" }),
    h("div", { class: "tx" }, title ? h("b", { text: title + " " }) : null, body ? h("span", { text: body }) : null), btn || null);
}
function allowBtn(server) {
  return h("button", { class: "act nb", type: "button", text: t("fixAllow"), onclick: function () {
    claude.use("permissions").then(function (p) { return p && p.request(["mcp:" + server]); }).catch(function () {}).then(function () { refresh(); }); } });
}
function earlierPending() {  // closes from an earlier visit not yet in the registry (this visit's own sit in their undo window)
  return Object.keys(MEM.closing).filter(function (id) { return !MEM.closing[id].written && !timers[id]; }).sort();
}
function stateNotice() {
  if (ST.phase === "nomcp") return notice("calm", t("noMcpT"), t("noMcpP"));
  if (ST.phase === "ms") return notice("calm", t("msT"), t("msP"));
  if (ST.err.drive) { var c = ST.err.drive.code;
    return notice("red", t("discT"), errText(ST.err.drive, SRV.drive), (c === "not_in_manifest" || c === "approval_required") ? allowBtn(SRV.drive) : null); }
  var ep = earlierPending();
  if (ep.length && mcp) return notice("calm", t("pendingT"), t("pendingP", { ids: ep.join(", ") }));
  if (stale()) return notice("amber", t("staleT", { w: dlong(radarDate()) }), t("staleP"), h("button", { class: "act nb", type: "button", onclick: function () { toast(t("staleFix")); }, text: t("fix") }));
  return null;
}
function skRows(n) { var out = []; for (var i = 0; i < n; i++) out.push(h("div", { class: "skrow" }, h("span", { class: "c" }), h("span", { class: "l" }, h("span", { class: "skel", style: "width:" + (62 + i * 9 % 30) + "%" }), h("span", { class: "skel", style: "width:" + (34 + i * 13 % 30) + "%;height:10px" })), h("span", { class: "skel" }))); return h("div", { class: "list" }, out); }
function listEmpty(kind) {
  if (ST.phase === "loading") return skRows(kind === "todo" ? 4 : 3);
  if (ST.phase === "first") return h("div", { class: "empty", text: t(kind === "todo" ? "firstEmpty" : kind === "dele" ? "firstEmptyDele" : "firstEmptyFyi") });
  if (!ST.model) return h("div", { class: "empty", text: ST.phase === "nomcp" ? t("noMcpT") : ST.phase === "ms" ? t("msT") : t("discList", { c: PROV.conn }) });
  return null;
}

/* ---------- rows ---------- */
function actOf(x) { return x.kind === "decide" ? "decide" : (x.threadId && ST.canDraft) ? "reply" : safeUrl(x.link) ? "open" : null; }
function kindLabel(k) { return t("k_" + k); }
function todoRow(x, withAct) {
  var a = actOf(x), done = status(x) === "done", closedRow = x.closedOn !== undefined;
  var label = a === "decide" ? t("decide") : a === "reply" ? t("reply") : t("openBtn");
  var sub = [closedRow ? null : kindLabel(x.kind), x.who, x.why].filter(Boolean).join(" · ");
  return h("div", { class: "row" + (done ? " done" : ""), role: "button", tabindex: "0", onclick: function () { if (!closedRow) openSheet(x, "todo"); },
    onkeydown: function (e) { if (e.key === "Enter" && !closedRow) openSheet(x, "todo"); } },
    closedRow ? h("span", { class: "stc done", "aria-label": t("st_done") }, h("span", { class: "ring" })) : stc(x, "todo"),
    h("div", {}, h("div", { class: "tt", text: x.title }), sub ? h("div", { class: "ss", text: sub }) : null),
    h("div", { class: "rt" }, prepared(x) ? h("span", { class: "chip ready", text: t("draftReady") }) : null, signal(x, false), withAct && a && !done ? h("button", { class: "act pri", type: "button", onclick: function (e) {
      e.stopPropagation(); if (a === "open") openUrl(x.link); else openSheet(x, "todo", a === "reply" ? "reply" : null); }, text: label }) : null));
}
function deleRow(x) {
  return h("div", { class: "row" + (status(x) === "done" ? " done" : ""), role: "button", tabindex: "0", onclick: function () { openSheet(x, "dele"); }, onkeydown: function (e) { if (e.key === "Enter") openSheet(x, "dele"); } },
    stc(x, "dele"), h("div", {}, h("div", { class: "tt", text: x.title }), h("div", { class: "ss" }, h("span", { class: "who" }, x.who ? h("span", { class: "av", text: initials(x.who) }) : null, [x.who, x.why].filter(Boolean).join(" · ")))),
    h("div", { class: "rt" }, signal(x, true)));
}

/* ---------- calendar ---------- */
function calendar() {
  var wrap = h("div", {}), wh = hours();
  var START = Math.floor(Math.min.apply(null, [wh[0]].concat(ST.meetings.map(function (m) { return mm(m.t); }))) / 60);
  var END = Math.ceil(Math.max.apply(null, [wh[1]].concat(ST.meetings.map(function (m) { return mm(m.e); }))) / 60);
  var H = 40, nm = mm(parts(new Date()).hm);
  var busy = ST.meetings.reduce(function (a, m) { return a + Math.max(0, mm(m.e) - mm(m.t)); }, 0);
  var calOk = ST.calOn && !ST.err.cal && ST.phase !== "loading" && ST.phase !== "nomcp";
  wrap.append(h("div", { class: "cal-h" }, h("h2", {}, h("a", { class: "calink", href: PROV.calUrl, target: "_blank", rel: "noopener", title: t("openCal", { c: PROV.cal }) }, t("calendar"), svg(ICON.ext))),
    calOk ? h("span", { class: "s", text: t("calSum", { m: ST.meetings.length, h: Math.max(0, Math.round((wh[1] - wh[0] - busy) / 30) / 2) }) }) : null));
  if (ST.phase === "loading") { wrap.append(h("div", { class: "skel", style: "height:" + ((END - START) * H) + "px;border-radius:8px" })); return wrap; }
  if (!calOk) { wrap.append(h("div", { class: "empty", style: "border:1px dashed var(--line);border-radius:8px", text: !ST.calOn ? t("noCal") : ST.err.cal ? errText(ST.err.cal, SRV.cal) : t("noMcpT") })); return wrap; }
  var cal = h("div", { class: "cal", style: "height:" + ((END - START) * H) + "px" });
  for (var hr = START; hr <= END; hr++) cal.append(h("div", { class: "hr", style: "top:" + ((hr - START) * H) + "px" }, h("span", { text: String(hr).padStart(2, "0") + ":00" })));
  function place(a, b) { var top = (mm(a) - START * 60) / 60 * H, ht = Math.max(22, (mm(b) - mm(a)) / 60 * H - 3); return "top:" + (top + 1) + "px;height:" + ht + "px"; }
  ST.free.forEach(function (f) { var long = mm(f.e) - mm(f.t) >= 60;
    cal.append(h("button", { class: "ev free", type: "button", style: place(f.t, f.e), onclick: function () { toast(t("pickTodo", { r: f.t + "–" + f.e })); go("todo"); } },
      h("span", { class: "et", text: t("free") + " " + f.t + "–" + f.e }), long && f.use ? h("span", { class: "em", text: f.use }) : null)); });
  ST.meetings.forEach(function (m) { var past = mm(m.e) <= nm, short = mm(m.e) - mm(m.t) < 45;
    cal.append(h("button", { class: "ev meet" + (past ? " past" : ""), type: "button", style: place(m.t, m.e), onclick: function () { openUrl(m.link); } },
      h("span", { class: "et", text: short ? m.t + " " + m.title : m.title }), short ? null : h("span", { class: "em", text: m.t + "–" + m.e + (m.sub ? " · " + m.sub : "") }))); });
  if (nm >= START * 60 && nm <= END * 60) cal.append(h("div", { class: "nowl", style: "top:" + ((nm - START * 60) / 60 * H) + "px" }));
  wrap.append(cal, h("div", { class: "cal-legend" }, h("span", {}, h("i", { style: "background:var(--accent-soft);border:1px solid rgba(35,131,226,.28)" }), t("legMeet")),
    h("span", {}, h("i", { style: "border:1.5px dashed var(--faint)" }), ST.brief ? t("legFree") : t("free"))));
  return wrap;
}

/* ---------- views ---------- */
function allDone() {
  var dn = todoAll().filter(function (x) { return x.id && MEM.closing[x.id] && dd(parts(new Date(MEM.closing[x.id].at)).date, today()) === 0; });
  var next = ST.model && ST.model.at ? hhmm((mm(ST.model.at.slice(11, 16)) + 120) % 1440) : "";
  return h("div", { class: "alldone" }, h("div", { class: "ad-h" }, h("span", { class: "stc done" }, h("span", { class: "ring" })), h("h3", { text: t("allDoneT") })),
    h("p", { text: dn.length ? t("allDoneP", { n: dn.length, t: next }) : t("allDoneP0", { t: next }) }),
    dn.length ? h("div", { class: "list" }, dn.map(function (x) { return todoRow(x, false); })) : null);
}
function vToday() {
  var hr = +parts(new Date()).hm.slice(0, 2), greet = hr < 12 ? t("gm") : hr < 19 ? t("ga") : t("ge");
  var name = (ST.model && ST.model.owner) || CFG.owner.name || "";
  var v = h("div", { class: "view wide" }, h("p", { class: "eyebrow", text: fmt(today(), { weekday: "long", day: "numeric", month: "long" }) }),
    h("h1", { class: "v-h1", text: name ? greet + ", " + name.split(" ")[0] : greet }));
  var n = stateNotice(); if (n) v.append(n);
  var hasFocus = ST.phase === "first" || ST.phase === "loading" || (hasData() && ST.brief && ST.brief.focus);
  var grid = h("div", { class: "tgrid" + (hasFocus ? "" : " nofocus") }); v.append(grid);
  if (ST.phase === "first") {
    grid.append(h("div", { class: "a-focus welcome" }, h("h2", { text: t("firstT") }), h("p", { text: t("firstP") }),
      h("ul", { class: "steps" }, h("li", {}, h("span", { class: "stc done" }, h("span", { class: "ring" })), t("firstS1", { p: PROV.name })),
        h("li", {}, h("span", { class: "spin", "aria-hidden": "true" }), t("firstS2")), h("li", { class: "wait" }, h("span", { class: "stc todo" }, h("span", { class: "ring" })), t("firstS3")))));
    grid.append(h("div", { class: "a-cal" }, calendar())); return v;
  }
  if (ST.phase === "loading") grid.append(h("div", { class: "a-focus focus" }, h("div", { style: "flex:1;display:flex;flex-direction:column;gap:8px" }, h("span", { class: "skel", style: "width:30%;height:10px" }), h("span", { class: "skel", style: "width:90%" }), h("span", { class: "skel", style: "width:60%" }))));
  else if (hasData() && ST.brief && ST.brief.focus) grid.append(h("div", { class: "a-focus focus" }, h("div", {}, h("div", { class: "k", text: t("focus") }), h("p", { text: ST.brief.focus }))));
  grid.append(h("div", { class: "a-cal" }, calendar()));
  var top = rankTodo(openTodo()).slice(0, 3);
  grid.append(h("div", { class: "blk a-needs" }, h("div", { class: "blk-h" }, h("h2", { text: t("needs") }),
    hasData() ? h("button", { class: "more", type: "button", onclick: function () { go("todo"); }, text: t("allTodos", { n: openTodo().length }) }) : null),
    listEmpty("todo") || (top.length ? h("div", { class: "list" }, top.map(function (x) { return todoRow(x, true); })) : allDone())));
  if (hasData()) {
    var od = overdueDele().length, fyi = infoLeft().length, doneN = doneTodo().length;
    var elseBlk = h("div", { class: "blk a-else" }); grid.append(elseBlk);
    elseBlk.append(h("div", { class: "blk-h" }, h("h2", { text: t("else") })), h("div", { class: "sum" },
      h("button", { type: "button", onclick: function () { go("delegated"); } }, h("span", { class: "n" + (od ? " red" : ""), text: String(od) }), h("span", { class: "l", text: od === 1 ? t("sumDele1") : t("sumDele") }), h("span", { class: "chev", text: "›" })),
      h("button", { type: "button", onclick: function () { go("fyi"); } }, h("span", { class: "n", text: String(fyi) }), h("span", { class: "l", text: t("sumFyi") }), h("span", { class: "chev", text: "›" })),
      h("button", { type: "button", onclick: function () { todoFilter = "done"; go("todo"); } }, h("span", { class: "n", text: String(doneN) }), h("span", { class: "l", text: t("sumDone") }), h("span", { class: "chev", text: "›" }))));
    var props = ST.proposals.filter(function (pr) { return !MEM.answered[pr.id]; });
    if (props.length) elseBlk.append(h("div", { class: "sugg" }, h("div", { class: "blk-h" }, h("h2", { text: t("sugT") })),
      h("p", { class: "v-sub", text: t("sugP") }), h("div", { class: "list" }, props.map(function (pr) {
        return h("div", { class: "irow" }, h("div", {}, h("div", { class: "tt", text: pr.rule }), pr.from ? h("div", { class: "ss", text: t("ruleFrom", { f: pr.from }) }) : null),
          h("div", { class: "rt" }, h("button", { class: "act pri", type: "button", onclick: function () { answerProposal(pr, true); }, text: t("keepRule") }),
            h("button", { class: "ghost", type: "button", onclick: function () { answerProposal(pr, false); }, text: t("dismissRule") }))); }))));
  }
  return v;
}
function vTodo() {
  var v = h("div", { class: "view" }, h("h1", { class: "v-h1", text: t("todo") }), h("p", { class: "v-sub", text: t("todoSub") }));
  var n = stateNotice(); if (n) v.append(n);
  var e = listEmpty("todo"); if (e) { v.append(e); return v; }
  var sz = snoozedAll(), segs = sz.length ? ["open", "snoozed", "done"] : ["open", "done"];
  if (todoFilter === "snoozed" && !sz.length) todoFilter = "open";
  v.append(h("div", { class: "vtools" }, h("span", { class: "seg", role: "group" }, segs.map(function (f) {
    return h("button", { type: "button", "aria-pressed": String(todoFilter === f), onclick: function () { todoFilter = f; render(); },
      text: f === "open" ? t("open") + " (" + openTodo().length + ")" : f === "snoozed" ? t("snoozedTab") + " (" + sz.length + ")" : t("done") }); }))));
  if (todoFilter === "snoozed") {
    v.append(h("div", { class: "list" }, sz.sort(function (a, b) { return snoozed(a) < snoozed(b) ? -1 : 1; }).map(function (x) {
      return h("div", { class: "row", role: "button", tabindex: "0", onclick: function () { openSheet(x, x.kind ? "todo" : "dele"); } },
        h("span", { class: "stc todo" }, h("span", { class: "ring" })), h("div", {}, h("div", { class: "tt", text: x.title }), x.who ? h("div", { class: "ss", text: x.who }) : null),
        h("div", { class: "rt" }, h("span", { class: "sig", text: t("snoozedUntil", { d: dlong(snoozed(x)) }) }))); })));
    return v;
  }
  var list = todoFilter === "open" ? rankTodo(openTodo()) : doneTodo();
  if (!list.length) { v.append(h("div", { class: "empty", text: todoFilter === "open" ? t("allClear") : t("noneDone") })); return v; }
  var days = {};
  list.forEach(function (x) {
    var c = x.id && MEM.closing[x.id], d = c ? parts(new Date(c.at)).date : x.closedOn || x.since || radarDate() || today(); var k = dd(d, today()) > 6 ? "earlier" : d; (days[k] = days[k] || []).push(x); });
  Object.keys(days).sort(function (a, b) { return a === "earlier" ? 1 : b === "earlier" ? -1 : a < b ? 1 : -1; }).forEach(function (k) {
    v.append(h("div", { class: "grp" }, h("span", { text: k === "earlier" ? t("earlier") : rel(k) }), h("span", { class: "n", text: String(days[k].length) })),
      h("div", { class: "list" }, days[k].map(function (x) { return todoRow(x, false); }))); });
  return v;
}
function vDele() {
  var v = h("div", { class: "view" }, h("h1", { class: "v-h1", text: t("delegated") }), h("p", { class: "v-sub", text: t("deleSub") }));
  var n = stateNotice(); if (n) v.append(n);
  var e = listEmpty("dele"); if (e) { v.append(e); return v; }
  var over = overdueDele(), all = ST.model.dele;
  var groups = [["gOver", over], ["gWait", openDele().filter(function (x) { return over.indexOf(x) < 0 && status(x) === "todo"; })],
    ["gDoing", openDele().filter(function (x) { return over.indexOf(x) < 0 && status(x) === "doing"; })], ["gDone", all.filter(function (x) { return status(x) === "done"; })]];
  var any = false;
  groups.forEach(function (g) { if (!g[1].length) return; any = true; g[1].sort(function (a, b) { return (a.since || "9") < (b.since || "9") ? -1 : 1; });
    v.append(h("div", { class: "grp" }, h("span", { text: t(g[0]) }), h("span", { class: "n", text: String(g[1].length) })), h("div", { class: "list" }, g[1].map(deleRow))); });
  if (!any) v.append(h("div", { class: "empty", text: t("noDele") }));
  return v;
}
function vFyi() {
  var v = h("div", { class: "view" }, h("h1", { class: "v-h1", text: t("fyi") }), h("p", { class: "v-sub", text: t("fyiSub") }));
  var n = stateNotice(); if (n) v.append(n);
  var e = listEmpty("fyi"); if (e) { v.append(e); return v; }
  var left = infoLeft(), hid = ST.model.info.length - left.length;
  if (hid) v.append(h("div", { class: "vtools" }, h("span", { class: "chip", text: t("readN", { n: hid }) }),
    h("button", { class: "ghost", type: "button", onclick: function () { ST.model.info.forEach(function (i) { delete MEM.read[i.key]; }); save(); render(); }, text: t("showAgain") })));
  if (!left.length) { v.append(h("div", { class: "empty", text: t("upToDate") })); return v; }
  var tp = {}; left.forEach(function (i) { (tp[i.topic] = tp[i.topic] || []).push(i); });
  Object.keys(tp).sort().forEach(function (k) {
    v.append(k ? h("div", { class: "topic", text: k }) : null, h("div", { class: "list" }, tp[k].map(function (i) {
      var u = safeUrl(i.link);
      return h("div", { class: "irow" }, h("div", {}, h("div", { class: "tt", text: i.title }), i.detail || u ? h("div", { class: "ss" }, i.detail || null,
        u ? h("a", { href: u, target: "_blank", rel: "noopener", text: (i.detail ? " · " : "") + t("openSrc") }) : null) : null),
        h("button", { class: "ghost", type: "button", onclick: function () { MEM.read[i.key] = 1; save(); render();
          toast(t("markedRead"), { label: t("undo"), fn: function () { delete MEM.read[i.key]; save(); render(); } }); }, text: t("gotIt") }));
    }))); });
  return v;
}

/* ---------- detail sheet ---------- */
var sheetOpen = null;
function closeSheet() { sheetOpen = null; var s = document.getElementById("sheet"); s.classList.remove("on"); s.setAttribute("aria-hidden", "true"); document.getElementById("scrim").classList.remove("on"); }
function openSheet(x, set, mode) {
  sheetOpen = { x: x, set: set };
  var s = document.getElementById("sheet"); s.replaceChildren(); s.setAttribute("aria-label", x.title);
  var body = h("div", { class: "sh-body" }), st = status(x);
  s.append(h("div", { class: "sh-top" }, h("span", { class: "chip", text: set === "dele" ? t("k_dele") : kindLabel(x.kind) }), x.id ? h("span", { class: "pend", text: x.id }) : null,
    h("button", { class: "ghost x", type: "button", onclick: closeSheet, text: t("close") })), body);
  body.append(h("h2", { class: "sh-title", text: x.title }), h("div", { class: "stsel", role: "group" }, ["todo", "doing", "done"].map(function (k) {
    return h("button", { type: "button", "aria-pressed": String(st === k), onclick: function () { if (st !== k) setStatus(x, k, set); } }, h("span", { class: "stc " + k }, h("span", { class: "ring" })), stLabel(set, k)); })));
  if (x.why) body.append(h("p", { class: "sh-why", text: x.why }));
  var f = h("div", { class: "facts" }); function fact(k, v) { f.append(h("div", { class: "k", text: k }), h("div", {}, v)); }
  if (x.who) fact(set === "dele" ? t("f_asked") : t("f_from"), h("span", { class: "who" }, h("span", { class: "av", text: initials(x.who) }), x.who));
  fact(t("f_due"), x.due ? (function () { var n = dd(today(), x.due); return dlong(x.due) + (n < 0 ? " · " + t("daysOver", { n: -n }) : n === 0 ? " · " + t("todayL") : ""); })() : t("noDeadline"));
  if (x.since) fact(set === "dele" ? t("f_since") : t("f_first"), set === "dele" ? dlong(x.since) + " · " + t("days", { n: waited(x) }) : rel(x.since));
  var u = safeUrl(x.link); if (u) fact(t("f_src"), h("a", { href: u, target: "_blank", rel: "noopener", text: t("openSrc") }));
  body.append(f);
  var ld = looksDone(x);
  if (ld) {  // evidence, then the user's call
    var lu = safeUrl(ld.link);
    body.append(h("div", { class: "evidence" }, h("div", { class: "k", text: t("looksDoneT") }),
      h("p", {}, ld.text + (ld.date ? " (" + rel(ld.date) + ")" : ""), lu ? h("a", { href: lu, target: "_blank", rel: "noopener", text: " " + t("seeIt") }) : null),
      h("div", { class: "qlabel", text: t("looksDoneAsk") }),
      h("div", { class: "pair" }, h("button", { class: "bigbtn pri", type: "button", onclick: function () { requestClose(x, "done"); }, text: t("yesDone") }),
        h("button", { class: "bigbtn", type: "button", onclick: function () { requestClose(x, "keep open"); }, text: t("notYet") }))));
  }
  var acts = h("div", { class: "acts" }); body.append(acts);
  var canMail = ST.canDraft && (x.threadId || set === "dele" || x.kind === "decide");
  var prep = prepared(x);
  if (set === "todo" && x.kind === "decide" && canMail) {
    acts.append(h("div", { class: "qlabel", text: t("decideQ") }), h("div", { class: "decide" },
      h("button", { class: "bigbtn", type: "button", onclick: function () { compose(body, x, "accept", acts); }, text: t("accept") }),
      h("button", { class: "bigbtn", type: "button", onclick: function () { compose(body, x, "decline", acts); }, text: t("decline") }),
      h("button", { class: "bigbtn", type: "button", onclick: function () { compose(body, x, "time", acts); }, text: t("moreTime") })));
  } else if (canMail) {
    var main = set === "dele" ? ["follow", t("follow")] : prep ? ["prepared", t("reviewDraft")] : ["reply", t("reply")];
    acts.append(h("button", { class: "bigbtn pri", type: "button", onclick: function () { compose(body, x, main[0], acts); }, text: main[1] }));
  } else if (u) {
    acts.append(h("button", { class: "bigbtn pri", type: "button", onclick: function () { openUrl(u); } },
      /mail\.google\./.test(u) ? t("openIn", { m: PROV.mail }) : t("openSrc"), svg(ICON.ext)));
    if (!ST.canDraft && CFG.email === "gmail") acts.append(h("div", { class: "blocked", text: t("noDrafts") }));
  }
  acts.append(h("div", { class: "pair" }, ST.canEvent ? h("button", { class: "bigbtn", type: "button", onclick: function () { block(body, x, acts); }, text: t("block") }) : null,
    h("button", { class: "bigbtn", type: "button", onclick: function () { requestClose(x, "not mine"); }, text: t("notMine") })));
  var d0 = today(), dow = new Date(d0 + "T12:00:00Z").getUTCDay(), toMon = ((8 - dow) % 7) || 7;
  acts.append(h("div", { class: "qlabel", text: t("snooze") }), h("div", { class: "decide" },
    [["snoozeTomorrow", addDays(d0, 1)], ["snoozeMonday", addDays(d0, toMon)], ["snoozeNextWeek", addDays(d0, 7)]].map(function (o) {
      return h("button", { class: "bigbtn", type: "button", onclick: function () { requestClose(x, "snooze until " + o[1]); }, text: t(o[0]) }); })));
  acts.append(h("div", { class: "why-note", text: t("neverSent") }));
  s.classList.add("on"); s.setAttribute("aria-hidden", "false"); document.getElementById("scrim").classList.add("on");
  if (mode === "reply" && canMail) compose(body, x, prep ? "prepared" : "reply", acts);
  setTimeout(function () { var b = s.querySelector(".x"); if (b) b.focus(); }, 60);
}
function emailOf(s) { var m = /<([^>]+@[^>]+)>/.exec(s || "") || /([^\s<>"]+@[^\s<>"]+)/.exec(s || ""); return m ? m[1] : ""; }
function compose(body, x, m, acts) {
  acts.hidden = true;
  var first = String(x.who || "").split(/[\s(]/)[0], me = String(CFG.owner.name || "").split(" ")[0];
  var tpl = m === "prepared" ? "reply" : m;
  var text = (STR.DRAFT[LANG] || STR.DRAFT.en)[tpl].split("{f}").join(first || "").split("{me}").join(me).replace(/^(Hi|Hola) ,/, "$1,").replace(/^(Hola) :/, "$1:");
  var ref = { msgId: null };
  var to = h("input", { type: "email", autocomplete: "off" }), subj = h("input", { type: "text", value: x.title }), msg = h("textarea", {}, text);
  var err = h("div", { class: "sh-err", hidden: true }), notes = h("ul", { class: "notes", hidden: true }), warned = false;
  var saveBtn = h("button", { class: "bigbtn pri", type: "button", text: t("saveDraft", { m: PROV.mail }), onclick: function () {
    var addr = to.value.trim(); if (!/^[^\s@]+@[^\s@]+$/.test(addr)) { err.textContent = t("toMissing"); err.hidden = false; to.focus(); return; }
    if (/\[[^\]\n]+\]/.test(msg.value) && !warned) {  // parts only the user can fill: say so once, save on the second press
      warned = true; err.textContent = t("placeholdersLeft"); err.hidden = false; msg.focus(); return;
    }
    saveBtn.disabled = true; err.hidden = true;
    var input = { to: [addr], subject: subj.value, body: msg.value }; if (ref.msgId) input.replyToMessageId = ref.msgId;
    mcp.callTool(SRV.mail, "create_draft", input).then(function (r) {
      var p = r.payload || {}; closeSheet();
      toast(t("draftSaved", { m: PROV.mail }), safeUrl(p.viewUrl) ? { label: t("openDraft"), fn: function () { openUrl(p.viewUrl); } } : null);
      if (m === "prepared" && ref.original != null && x.id) {  // teach learn how the user writes; it only ever proposes rules
        var same = ref.original.trim() === msg.value.trim();
        writeNote(same ? "learn — draft used" : "learn — draft edited", same ? { task: x.id } : { task: x.id, prepared: ref.original, saved: msg.value }).catch(function () {});
      }
      if (status(x) === "todo" && m !== "follow") { MEM.doing[x.key] = 1; save(); render(); }
    }).catch(function (e) { saveBtn.disabled = false; err.textContent = t("draftFail", { e: errText(e, SRV.mail) }); err.hidden = false; });
  } });
  var box = h("div", { class: "compose" }, h("div", { class: "hint", text: m === "follow" ? t("hintFollow") : m === "prepared" ? t("hintPrepared") : t("hintReply") }),
    h("label", {}, t("to"), to), h("label", {}, t("subject"), subj), h("label", {}, t("message"), msg), notes, err,
    h("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:8px" }, h("button", { class: "bigbtn", type: "button", onclick: function () { box.remove(); acts.hidden = false; }, text: t("cancel") }), saveBtn));
  body.append(box); msg.focus();
  if (m === "prepared") {  // the draft the prepare skill wrote for this task; the user edits and saves it
    var doc = prepared(x); msg.value = t("preparedLoading"); msg.disabled = true;
    readDoc(doc.id).then(function (txt) {
      var pd = R.parsePrepared(txt); msg.disabled = false;
      msg.value = pd.draft || text; if (pd.subject) subj.value = pd.subject; ref.original = pd.draft || null;
      if (pd.notes.length) { notes.replaceChildren.apply(notes, pd.notes.map(function (n) { return h("li", { text: n }); })); notes.hidden = false; }
    }).catch(function () { msg.disabled = false; msg.value = text; err.textContent = t("preparedFail"); err.hidden = false; });
  }
  if (x.threadId) {  // reply in the thread: last message from someone else
    mcp.callTool(SRV.mail, "get_thread", { threadId: x.threadId, messageFormat: "MINIMAL" }).then(function (r) {
      var msgs = ((r.payload || {}).messages || []).slice().reverse();
      var other = msgs.filter(function (z) { return (z.labelIds || []).indexOf("SENT") < 0; })[0] || msgs[0];
      if (!other) return;
      ref.msgId = other.id; if (!to.value) to.value = emailOf(other.sender);
      if (other.subject && (m !== "prepared" || !subj.value || subj.value === x.title)) subj.value = /^re:/i.test(other.subject) ? other.subject : "Re: " + other.subject;
    }).catch(function () { err.textContent = t("threadFail"); err.hidden = false; });
  }
}
function block(body, x, acts) {
  acts.hidden = true;
  var free = ST.free.filter(function (f) { return mm(f.e) > mm(parts(new Date()).hm); })[0];
  var day = h("select", {}, h("option", { value: "0", text: t("today") }), h("option", { value: "1", text: t("tomorrow") }));
  var start = h("input", { type: "time", value: free ? free.t : "14:00" });
  var len = h("select", {}, [["30", "30 min"], ["60", "1 h"], ["90", "90 min"]].map(function (o, i) { return h("option", { value: o[0], selected: i === 1, text: o[1] }); }));
  var err = h("div", { class: "sh-err", hidden: true });
  var add = h("button", { class: "bigbtn pri", type: "button", text: t("addCal"), onclick: function () {
    add.disabled = true; err.hidden = true;
    var d = addDays(today(), +day.value), a = mm(start.value || "14:00"), b = Math.min(a + +len.value, 1439);
    mcp.callTool(SRV.cal, "create_event", { summary: x.title, startTime: d + "T" + hhmm(a) + ":00", endTime: d + "T" + hhmm(b) + ":00", timeZone: TZ,
      availability: "AVAILABILITY_BUSY", notificationLevel: "NONE" }).then(function () {
      closeSheet(); toast(t("added")); if (d === today()) loadCalendar(true).then(function () { ST.free = freeBlocks(); render(); });
    }).catch(function (e) { add.disabled = false; err.textContent = t("eventFail", { e: errText(e, SRV.cal) }); err.hidden = false; });
  } });
  var box = h("div", { class: "compose" }, h("div", { class: "hint", text: t("hintBlock") }),
    h("div", { class: "row3" }, h("label", {}, t("day"), day), h("label", {}, t("start"), start), h("label", {}, t("length"), len)), err,
    h("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:8px" }, h("button", { class: "bigbtn", type: "button", onclick: function () { box.remove(); acts.hidden = false; }, text: t("cancel") }), add));
  body.append(box);
}
document.getElementById("scrim").addEventListener("click", closeSheet);
document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeSheet(); });

/* ---------- toast ---------- */
var tt = null;
function toast(m, action) {
  var el = document.getElementById("toast"); el.replaceChildren(h("span", { text: m }));
  if (action) el.append(h("button", { type: "button", onclick: function () { el.hidden = true; action.fn(); }, text: action.label }));
  el.hidden = false; clearTimeout(tt); tt = setTimeout(function () { el.hidden = true; }, action ? 6000 : 3400);
}

/* ---------- render + wiring ---------- */
function render() {
  document.documentElement.lang = LANG; renderNav();
  document.getElementById("main").replaceChildren(cur === "todo" ? vTodo() : cur === "delegated" ? vDele() : cur === "fyi" ? vFyi() : vToday());
  setSide(MEM.side);
}
var busyR = false;
function refresh() {
  if (busyR) return; busyR = true; var b = document.getElementById("refresh"); b.disabled = true; toast(t("refreshing"));
  var before = ST.radar && ST.radar.title;
  load(true).then(function () { busyR = false; b.disabled = false;
    if (ST.err.drive) toast(errText(ST.err.drive, SRV.drive));
    else if (ST.radar && ST.radar.title === before) toast(stale() ? t("checkedStale", { w: dlong(radarDate()) }) : t("checked", { t: ST.model.at.slice(11, 16) }));
    else document.getElementById("toast").hidden = true;
  });
}
document.getElementById("refresh").addEventListener("click", refresh);
var TOG = { open: '<rect x="3.5" y="4.5" width="17" height="15" rx="3"/><path d="M9.5 4.5v15M15.5 10l-2 2 2 2"/>', shut: '<rect x="3.5" y="4.5" width="17" height="15" rx="3"/><path d="M9.5 4.5v15M13.5 10l2 2-2 2"/>' };
function setSide(c) { var a = document.getElementById("app"), b = document.getElementById("tog"); a.classList.toggle("collapsed", c); b.replaceChildren(svg(c ? TOG.shut : TOG.open));
  b.setAttribute("aria-label", c ? t("expand") : t("collapse")); b.setAttribute("aria-expanded", String(!c)); b.title = c ? t("expand") : t("collapse"); }
document.getElementById("tog").addEventListener("click", function () { MEM.side = !MEM.side; save(); setSide(MEM.side); });

/* ---------- theme: Auto follows Claude's own theme (whatever the viewer set on this page), Light/Dark override it ---------- */
var HOST_THEME = document.documentElement.getAttribute("data-theme");
var THEME_ICON = { auto: '<circle cx="12" cy="12" r="8"/><path class="fill" d="M12 4a8 8 0 010 16z"/>',
  light: '<circle cx="12" cy="12" r="3.6"/><path d="M12 3v1.6M12 19.4V21M3 12h1.6M19.4 12H21M5.6 5.6l1.1 1.1M17.3 17.3l1.1 1.1M5.6 18.4l1.1-1.1M17.3 6.7l1.1-1.1"/>',
  dark: '<path d="M19.5 14.5A7.5 7.5 0 019.5 4.5a7.5 7.5 0 1010 10z"/>' };
var THEME_NEXT = { auto: "light", light: "dark", dark: "auto" };
function applyTheme() {
  var m = THEME_NEXT[MEM.theme] ? MEM.theme : "auto", root = document.documentElement;
  if (m === "auto") { if (HOST_THEME) root.setAttribute("data-theme", HOST_THEME); else root.removeAttribute("data-theme"); }
  else root.setAttribute("data-theme", m);
  var label = t("theme") + ": " + t("th_" + m) + ". " + t("th_next", { n: t("th_" + THEME_NEXT[m]) });
  ["theme", "mtheme"].forEach(function (id) { var b = document.getElementById(id); if (!b) return;
    b.replaceChildren(svg(THEME_ICON[m])); b.setAttribute("aria-label", label); b.title = label; });
}
["theme", "mtheme"].forEach(function (id) { document.getElementById(id).addEventListener("click", function () {
  MEM.theme = THEME_NEXT[MEM.theme] || "light"; save(); applyTheme(); }); });
new MutationObserver(function () {  // Claude's theme changed: remember it for Auto, keep an explicit choice on top
  var cur = document.documentElement.getAttribute("data-theme"), m = MEM.theme || "auto";
  if (m === "auto") { HOST_THEME = cur; return; }
  if (cur !== m) { HOST_THEME = cur; document.documentElement.setAttribute("data-theme", m); }
}).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
applyTheme();
document.addEventListener("visibilitychange", function () { if (document.visibilityState === "visible" && booted && mcp) load(false); });
window.addEventListener("hashchange", function () { go(location.hash.slice(1)); });
go((location.hash || "#today").slice(1));
load(false);
})();
