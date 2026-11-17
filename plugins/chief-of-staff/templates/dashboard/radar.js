/* Chief of Staff dashboard: parse registry documents into the board's model.
 * Pure functions, no DOM, no network. build_dashboard.py inlines this file
 * into the page; tests run it under Node against tests/fixtures/task-ids/.
 * Rules: references/dashboard.md (Data) and registry-layout.md (radar run). */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CosRadar = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var SECTIONS = ["Owner", "Journal", "Needs you now", "Decide", "Today", "Open loops", "I owe",
    "Waiting on", "Closed", "Moving", "Watching", "Handoff", "Cursors", "Trace",
    "Your day", "Due or overdue", "Free blocks"];  // the last three are brief sections
  var TASK_RE = /^T-([1-9]\d*)\s+—\s+(.*)$/;
  var LINK_RE = /<?(https?:\/\/[^\s<>]+)>?/;
  var DATE_RE = /\b(\d{4}-\d{2}-\d{2})\b/g;
  var DUE_RE = /\bdue (\d{4}-\d{2}-\d{2})\b/;
  var REASONS = /^(done|not mine|resolved|expired)$/i;  // Closed reasons, English in every language
  var RADAR_TITLE_RE = /^(\d{4}-\d{2}-\d{2}) (\d{2})(\d{2}) radar$/;
  var BRIEF_TITLE_RE = /^(\d{4}-\d{2}-\d{2}) (\d{2})(\d{2}) brief$/;

  function unescapeMd(s) { return s.replace(/\\([\[\]()*_`#>\\-])/g, "$1"); }
  function stripMd(s) { return unescapeMd(s).replace(/\*\*?([^*]+)\*\*?/g, "$1").trim(); }

  function sectionOf(line) {
    if (/^\s*[-*•]\s/.test(line)) return null;
    var m = /^\s*#{0,6}\s*([A-Za-z][A-Za-z ]*?)\s*(\(.*\))?\s*$/.exec(line);
    if (!m) return null;
    var name = m[1].toLowerCase();
    for (var i = 0; i < SECTIONS.length; i++) if (SECTIONS[i].toLowerCase() === name) return SECTIONS[i];
    return null;
  }

  /** Split a document into {section: [bullet text, ...]}. */
  function sections(text) {
    var out = {}, cur = null;
    String(text || "").split(/\r?\n/).forEach(function (raw) {
      var s = sectionOf(raw);
      if (s) { cur = s; out[cur] = out[cur] || []; return; }
      var b = /^\s*[-*•]\s+(.*)$/.exec(raw);
      if (cur && b) out[cur].push(b[1].trim());
    });
    return out;
  }

  /** One bullet -> {id, title, fields, link, due, dates}. Free-text fields stay in order. */
  function item(body) {
    var id = null, rest = body, m = TASK_RE.exec(body);
    if (m) { id = "T-" + m[1]; rest = m[2]; }
    var link = null, due = null, dates = [], fields = [];
    rest.split(/\s+—\s+/).forEach(function (part) {
      var p = part.trim();
      if (!p) return;
      var lm = LINK_RE.exec(p);
      if (lm && p.replace(LINK_RE, "").trim() === "") { link = link || lm[1]; return; }
      var dm = DUE_RE.exec(p);
      if (dm && p.replace(DUE_RE, "").trim() === "") { due = dm[1]; return; }
      var only = p.replace(DATE_RE, "").replace(/[^\p{L}]/gu, "");
      var ds = p.match(DATE_RE);
      if (ds && only.length <= 12) { dates = dates.concat(ds); return; }  // "since 2026-10-21", "des del 2026-10-21"
      if (lm) link = link || lm[1];
      fields.push(stripMd(p.replace(LINK_RE, "").trim()));
    });
    return { id: id, title: fields[0] || "", fields: fields.slice(1), link: link, due: due, dates: dates };
  }

  function isNote(body) { return body.indexOf("—") < 0 && !TASK_RE.test(body); }  // "none", "Cap.", "Res nou…"

  function topicOf(text) {
    var m = /^\[([^\]]+)\]\s*/.exec(text);
    return m ? { topic: m[1], text: text.slice(m[0].length) } : { topic: "", text: text };
  }

  function gmailThreadId(link) {
    var m = /#[^/]*\/thread-f:(\d+)/.exec(link || "");
    if (!m || typeof BigInt === "undefined") return null;
    try { return BigInt(m[1]).toString(16); } catch (e) { return null; }
  }

  function hash(s) {  // stable key for items without a task ID (FYI "Got it")
    var h = 5381;
    for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
    return "h" + (h >>> 0).toString(36);
  }

  /** Newest radar text -> the board's model. */
  function parseRadar(text) {
    var s = sections(text);
    var list = function (name) { return (s[name] || []).filter(function (b) { return !isNote(b); }); };
    var todo = [], byId = {}, closed = [], dele = [], info = [];

    function push(kind, body) {
      var it = item(body), key = it.id || hash(kind + body);
      if (byId[key]) {  // a task listed in Needs you now and in a loop section is one task
        var seen = byId[key];
        if (!seen.who && kind !== "needs") seen.who = it.fields[0] || "";
        seen.due = seen.due || it.due; seen.link = seen.link || it.link;
        seen.since = seen.since || it.dates[it.dates.length - 1] || null;
        seen.threadId = seen.threadId || gmailThreadId(it.link);
        return;
      }
      var who = "", why = "";
      if (kind === "needs") why = it.fields[0] || "";
      else if (kind === "decide") { who = it.fields[0] || ""; why = it.fields.slice(1).join(" — "); }
      else { who = it.fields[0] || ""; why = it.fields.slice(1).join(" — "); }
      var x = { key: key, id: it.id, kind: kind, title: it.title, who: who, why: why, link: it.link,
        due: it.due, since: it.dates[it.dates.length - 1] || null, threadId: gmailThreadId(it.link) };
      byId[key] = x;
      todo.push(x);
    }
    list("Needs you now").forEach(function (b) { push("needs", b); });
    list("Decide").forEach(function (b) { push("decide", b); });
    list("I owe").forEach(function (b) { push("owe", b); });
    list("Waiting on").forEach(function (b) {
      var it = item(b);
      dele.push({ key: it.id || hash("w" + b), id: it.id, title: it.title, who: it.fields[0] || "",
        why: it.fields.slice(1).join(" — "), link: it.link, due: it.due,
        since: it.dates[it.dates.length - 1] || null, threadId: gmailThreadId(it.link) });
    });
    list("Closed").forEach(function (b) {
      var it = item(b), f = it.fields.slice(), reason = "";
      if (f.length && REASONS.test(f[f.length - 1])) reason = f.pop().toLowerCase();
      var all = b.replace(DUE_RE, "").match(DATE_RE) || [];
      closed.push({ key: it.id || hash("c" + b), id: it.id, title: it.title, who: f[0] || "",
        reason: reason, note: f.slice(1).join(" — "), closedOn: all[all.length - 1] || null, link: it.link });
    });
    list("Watching").concat((s["Moving"] || []).filter(function (b) { return !/^(none|cap|ninguno|res)\.?$/i.test(b); }))
      .forEach(function (b) {
        var it = item(b), t = topicOf(unescapeMd(it.title));
        info.push({ key: it.id || hash("i" + b), id: it.id, topic: t.topic, title: stripMd(t.text),
          detail: it.fields.join(" — "), link: it.link });
      });
    var today = (s["Today"] || []).filter(function (b) { return !isNote(b); }).map(stripMd);
    var owner = (s["Owner"] || [])[0] || "";
    var head = /^#?\s*Radar · (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})/m.exec(String(text || ""));
    return { owner: stripMd(owner), todo: todo, dele: dele, closed: closed, info: info, today: today,
      at: head ? head[1] + "T" + head[2] : null };
  }

  /** Newest brief text -> {focus, free:[{from,to,use}]}. */
  function parseBrief(text) {
    var t = String(text || ""), f = /\*\*[^*]+:\*\*\s*(.+)/.exec(t), free = [];
    (sections(t)["Free blocks"] || []).forEach(function (line) {
      var m = /^(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})\s*(?:—\s*)?(.*)$/.exec(line);
      if (m) free.push({ from: m[1].padStart(5, "0"), to: m[2].padStart(5, "0"), use: stripMd(m[3] || "") });
    });
    return { focus: f ? stripMd(f[1]) : "", free: free };
  }

  /** Pick the newest document of a kind from search results by name, never by returned order. */
  function newest(files, kind) {
    var re = kind === "brief" ? BRIEF_TITLE_RE : RADAR_TITLE_RE;
    return (files || []).filter(function (f) { return f && re.test(f.title || ""); })
      .sort(function (a, b) { return a.title < b.title ? 1 : a.title > b.title ? -1 : 0; })[0] || null;
  }

  function titleTime(title) {
    var m = RADAR_TITLE_RE.exec(title || "") || BRIEF_TITLE_RE.exec(title || "");
    return m ? m[1] + "T" + m[2] + ":" + m[3] : null;
  }

  /** The handoff document the board writes for "Done" / "Not mine". */
  function handoff(taskId, reason, stamp) {
    return "# Handoff · " + stamp + "\n\n- instruction: close — " + reason + "\n- task: " + taskId +
      "\n- from: dashboard (on behalf of the user)\n";
  }

  return { sections: sections, item: item, parseRadar: parseRadar, parseBrief: parseBrief, newest: newest,
    titleTime: titleTime, handoff: handoff, gmailThreadId: gmailThreadId, hash: hash };
});
