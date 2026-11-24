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
  var PREPARED_TITLE_RE = /^(\d{4}-\d{2}-\d{2}) (\d{2})(\d{2}) prepared (T-[1-9]\d*)$/;

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
    var link = null, due = null, dates = [], fields = [], looksDone = null, keptOpen = null, snoozedUntil = null;
    rest.split(/\s+—\s+/).forEach(function (part) {
      var p = part.trim();
      if (!p) return;
      var ld = /^looks done:\s*(.*)$/i.exec(unescapeMd(p));
      if (ld) {  // evidence that the task is finished: the user confirms, the radar never closes it
        var lk = LINK_RE.exec(ld[1]), dm0 = /\((\d{4}-\d{2}-\d{2})\)/.exec(ld[1]);
        looksDone = { text: stripMd(ld[1].replace(LINK_RE, "").replace(/\(\d{4}-\d{2}-\d{2}\)/, "").trim()),
          date: dm0 ? dm0[1] : null, link: lk ? lk[1] : null };
        return;
      }
      var sz = /^snoozed until (\d{4}-\d{2}-\d{2})$/i.exec(p);
      if (sz) { snoozedUntil = sz[1]; return; }
      var ko = /^kept open (\d{4}-\d{2}-\d{2})$/i.exec(p);
      if (ko) { keptOpen = ko[1]; return; }
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
    return { id: id, title: fields[0] || "", fields: fields.slice(1), link: link, due: due, dates: dates,
      looksDone: looksDone, keptOpen: keptOpen, snoozedUntil: snoozedUntil };
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
        seen.looksDone = seen.looksDone || it.looksDone;
        seen.snoozedUntil = seen.snoozedUntil || it.snoozedUntil;
        return;
      }
      var who = "", why = "";
      if (kind === "needs") why = it.fields[0] || "";
      else if (kind === "decide") { who = it.fields[0] || ""; why = it.fields.slice(1).join(" — "); }
      else { who = it.fields[0] || ""; why = it.fields.slice(1).join(" — "); }
      var x = { key: key, id: it.id, kind: kind, title: it.title, who: who, why: why, link: it.link,
        due: it.due, since: it.dates[it.dates.length - 1] || null, threadId: gmailThreadId(it.link),
        looksDone: it.looksDone, snoozedUntil: it.snoozedUntil };
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
        since: it.dates[it.dates.length - 1] || null, threadId: gmailThreadId(it.link), looksDone: it.looksDone,
        snoozedUntil: it.snoozedUntil });
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

  /** Documents of a kind from search results, newest name first, never by returned order. */
  function byName(files, kind) {
    var re = kind === "brief" ? BRIEF_TITLE_RE : RADAR_TITLE_RE;
    return (files || []).filter(function (f) { return f && re.test(f.title || ""); })
      .sort(function (a, b) { return a.title < b.title ? 1 : a.title > b.title ? -1 : 0; });
  }
  function newest(files, kind) { return byName(files, kind)[0] || null; }

  /** A real radar starts with its `# Radar ·` header; a stub (e.g. only "PLACEHOLDER") does not. */
  function isRadar(text) { return /^\s*#?\s*Radar · \d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(String(text || "")); }

  /** The newest real radar: read by name, newest first, skipping stubs (registry-layout *Finding "the newest"*).
   *  read(id) -> Promise<text>. Resolves {file, text}, or null when the newest few are all stubs. */
  function newestRadar(files, read) {
    var list = byName(files, "radar").slice(0, 5);
    function at(i) {
      if (i >= list.length) return Promise.resolve(null);
      return Promise.resolve(read(list[i].id)).then(function (txt) { return isRadar(txt) ? { file: list[i], text: txt } : at(i + 1); });
    }
    return at(0);
  }

  /** Newest `prepared T-<n>` document per task: {"T-42": file}. */
  function preparedByTask(files) {
    var out = {};
    (files || []).forEach(function (f) {
      var m = PREPARED_TITLE_RE.exec((f && f.title) || "");
      if (m && (!out[m[4]] || out[m[4]].title < f.title)) out[m[4]] = f;
    });
    return out;
  }

  /** A `prepared` document -> {task, kind, subject, draft, notes[]}. */
  function parsePrepared(text) {
    var t = String(text || ""), out = { task: null, kind: "reply", subject: "", draft: "", notes: [] }, cur = null, draft = [];
    t.split(/\r?\n/).forEach(function (raw) {
      var h = /^\s*#{2,3}\s*(.+?)\s*$/.exec(raw);
      if (h && !/^\s*[-*•]\s/.test(raw)) { cur = h[1].toLowerCase(); return; }
      if (cur === null) {
        var kv = /^\s*[-*•]\s+(task|kind):\s*(.+)$/.exec(unescapeMd(raw));
        if (kv) out[kv[1]] = kv[2].trim();
        return;
      }
      if (cur === "subject" && raw.trim() && !out.subject) out.subject = unescapeMd(raw.trim());
      else if (cur === "draft") draft.push(unescapeMd(raw.replace(/^ {2}/, "")));
      else if (cur === "notes") { var b = /^\s*[-*•]\s+(.*)$/.exec(raw); if (b) out.notes.push(stripMd(b[1])); }
    });
    out.draft = draft.join("\n").replace(/^\n+|\n+$/g, "");
    return out;
  }

  /** Newest `lessons` document -> the proposed lessons waiting for the user. */
  function parseLessons(text) {
    var out = { proposed: [] }, cur = null;
    String(text || "").split(/\r?\n/).forEach(function (raw) {
      var h = /^\s*#{1,3}\s*(.+?)\s*$/.exec(raw);
      if (h && !/^\s*[-*•]\s/.test(raw)) { cur = h[1].toLowerCase(); return; }
      var b = /^\s*[-*•]\s+(.*)$/.exec(raw);
      if (cur !== "proposed" || !b) return;
      var m = /^(P-[1-9]\d*)\s+—\s+(.*)$/.exec(unescapeMd(b[1]).trim());
      if (!m) return;
      var parts = m[2].split(/\s+—\s+/), rule = stripMd(parts[0]), scope = "", from = "";
      parts.slice(1).forEach(function (f) {
        var s = /^scope:\s*(.+)$/.exec(f), fr = /^from:\s*(.+)$/.exec(f);
        if (s) scope = s[1].trim(); else if (fr) from = stripMd(fr[1].trim());
      });
      out.proposed.push({ id: m[1], rule: rule, scope: scope, from: from });
    });
    return out;
  }

  function newestLessons(files) {
    return (files || []).filter(function (f) { return /^\d{4}-\d{2}-\d{2} \d{4} lessons$/.test((f && f.title) || ""); })
      .sort(function (a, b) { return a.title < b.title ? 1 : -1; })[0] || null;
  }

  function titleTime(title) {
    var m = RADAR_TITLE_RE.exec(title || "") || BRIEF_TITLE_RE.exec(title || "");
    return m ? m[1] + "T" + m[2] + ":" + m[3] : null;
  }

  /** The handoff document the board writes for "Done" / "Not mine". */
  function handoff(taskId, reason, stamp) {  // reason: "done" | "not mine" | "keep open" | "snooze until YYYY-MM-DD"
    var instruction = reason === "keep open" || /^snooze until /.test(reason) ? reason : "close — " + reason;
    return "# Handoff · " + stamp + "\n\n- instruction: " + instruction + "\n- task: " + taskId +
      "\n- from: dashboard (on behalf of the user)\n";
  }

  /** Read back a task handoff (written here, on another device, or from chat): {task, reason} or null.
   *  reason uses the same words as handoff(): "done" | "not mine" | "keep open" | "snooze until YYYY-MM-DD". */
  function parseHandoff(text) {
    var s = String(text || "").replace(/\\([_*\-])/g, "$1");
    var task = /^\s*[-*]\s*task:\s*(T-\d+)\s*$/mi.exec(s), ins = /^\s*[-*]\s*instruction:\s*(.+?)\s*$/mi.exec(s);
    if (!task || !ins) return null;
    var i = ins[1].toLowerCase(), m;
    if ((m = /^close\s*[—–-]\s*(done|not mine)\b/.exec(i))) return { task: task[1], reason: m[1] };
    if (/^keep open\b/.test(i)) return { task: task[1], reason: "keep open" };
    if ((m = /^snooze until (\d{4}-\d{2}-\d{2})\b/.exec(i))) return { task: task[1], reason: "snooze until " + m[1] };
    return null;
  }

  /** `- paused: true` in a config document. */
  function isPaused(text) { return /^\s*[-*]\s*paused:\s*true\s*$/mi.test(String(text || "")); }

  /** One cron field ("*", "7", "8-20/2", "*\/30", "1-5", lists) against a number; null if unsupported. */
  function cronField(f, n, lo, hi) {
    var ok = false, bad = false;
    String(f).split(",").forEach(function (part) {
      var m = /^(\*|\d+)(?:-(\d+))?(?:\/(\d+))?$/.exec(part);
      if (!m) { bad = true; return; }
      var a = m[1] === "*" ? lo : +m[1], b = m[2] != null ? +m[2] : (m[1] === "*" || m[3] ? hi : a), st = m[3] ? +m[3] : 1;
      if (n >= a && n <= b && (n - a) % st === 0) ok = true;
    });
    return bad ? null : ok;
  }

  /** Was a scheduled run due in (from, to]? Times are "YYYY-MM-DD HH:MM" in the owner's timezone.
   *  Supports minute, hour and day-of-week fields (day-of-month and month must be "*"); null when it can't tell. */
  function dueBetween(cron, from, to) {
    var f = String(cron || "").trim().split(/\s+/);
    if (f.length !== 5 || f[2] !== "*" || f[3] !== "*" || !(from < to)) return null;
    var day = new Date(from.slice(0, 10) + "T00:00:00Z"), end = to.slice(0, 10);
    for (var guard = 0; guard < 15; guard++) {
      var d = day.toISOString().slice(0, 10);
      if (d > end) return false;
      var dow = cronField(f[4], day.getUTCDay(), 0, 7);
      if (dow === null) return null;
      if (!dow && day.getUTCDay() === 0) dow = cronField(f[4], 7, 0, 7);
      if (dow) for (var hr = 0; hr < 24; hr++) {
        var hOk = cronField(f[1], hr, 0, 23); if (hOk === null) return null; if (!hOk) continue;
        for (var mi = 0; mi < 60; mi++) {
          var mOk = cronField(f[0], mi, 0, 59); if (mOk === null) return null; if (!mOk) continue;
          var at = d + " " + String(hr).padStart(2, "0") + ":" + String(mi).padStart(2, "0");
          if (at > from && at <= to) return true;
        }
      }
      day.setUTCDate(day.getUTCDate() + 1);
    }
    return true;  // more than two weeks without a radar
  }

  /** Notes for `learn` and answers to proposed lessons (registry-layout.md, handoff). */
  function note(kind, fields, stamp) {
    // kind: "lesson — keep P-3" | "lesson — drop P-3" | "learn — draft used" | "learn — draft edited"
    var out = "# Handoff · " + stamp + "\n\n- instruction: " + kind;
    if (fields.task) out += "\n- task: " + fields.task;
    out += "\n- from: dashboard (on behalf of the user)\n";
    var cut = function (s) { s = String(s || ""); return s.length > 2000 ? s.slice(0, 2000) + "…" : s; };
    if (fields.prepared != null) out += "\n## Prepared\n\n" + cut(fields.prepared) + "\n";
    if (fields.saved != null) out += "\n## Saved\n\n" + cut(fields.saved) + "\n";
    return out;
  }

  return { sections: sections, item: item, parseRadar: parseRadar, parseBrief: parseBrief, newest: newest, byName: byName, isRadar: isRadar, newestRadar: newestRadar,
    titleTime: titleTime, handoff: handoff, parseHandoff: parseHandoff, isPaused: isPaused, dueBetween: dueBetween, preparedByTask: preparedByTask, parsePrepared: parsePrepared,
    parseLessons: parseLessons, newestLessons: newestLessons, note: note, gmailThreadId: gmailThreadId, hash: hash };
});
