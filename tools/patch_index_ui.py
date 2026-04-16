"""Patch templates/index.html and static/style.css for file feedback + progress."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
html = ROOT / "templates" / "index.html"
css = ROOT / "static" / "style.css"
t = html.read_text(encoding="utf-8")

old_label = """        <label class="file">
          <input type="file" id="file" name="file" accept=".json,.xlsx,.xls" required />
          <span>\u9009\u62e9\u6587\u4ef6</span>
        </label>"""

new_label = """        <label class="file">
          <input type="file" id="file" name="file" accept=".json,.xlsx,.xls" required />
          <span>\u9009\u62e9\u6587\u4ef6</span>
        </label>
        <p id="file-feedback" class="file-feedback" hidden></p>"""

if old_label not in t:
    raise SystemExit("index.html label block not found")
t = t.replace(old_label, new_label, 1)

old_status = """        <button type="submit" class="btn primary">\u5f00\u59cb\u5206\u7c7b</button>"""

new_status = """        <div id="progress-wrap" class="progress-wrap" hidden>
          <div class="progress-bar-outer" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
            <div id="progress-bar-inner" class="progress-bar-inner"></div>
          </div>
          <p id="progress-label" class="progress-label"></p>
        </div>
        <button type="submit" class="btn primary" id="submit-btn">\u5f00\u59cb\u5206\u7c7b</button>"""

if old_status not in t:
    raise SystemExit("submit button block not found")
t = t.replace(old_status, new_status, 1)

# Insert helpers + replace submit handler: find "form.addEventListener(\"submit\""
marker = '    form.addEventListener("submit", async (e) => {'
if marker not in t:
    raise SystemExit("submit listener not found")
idx = t.index(marker)
# find end of submit handler - match brace depth from idx
depth = 0
start = idx + len(marker) - 1  # position of {
end_pos = None
for i in range(idx, len(t)):
    if t[i] == "{":
        depth += 1
    elif t[i] == "}":
        depth -= 1
        if depth == 0:
            end_pos = i + 1
            break
if end_pos is None:
    raise SystemExit("could not find end of submit handler")

helpers = r'''    function formatBytes(n) {
      const x = Number(n);
      if (!Number.isFinite(x) || x < 0) return "";
      if (x < 1024) return x + " B";
      if (x < 1048576) return (x / 1024).toFixed(1) + " KB";
      return (x / 1048576).toFixed(1) + " MB";
    }

    const fileInputEl = document.getElementById("file");
    const fileFeedbackEl = document.getElementById("file-feedback");
    fileInputEl.addEventListener("change", () => {
      const f = fileInputEl.files[0];
      if (!f) {
        fileFeedbackEl.hidden = true;
        fileFeedbackEl.textContent = "";
        return;
      }
      fileFeedbackEl.hidden = false;
      fileFeedbackEl.textContent =
        "\u5df2\u9009\u62e9\uff1a" + f.name + " \uff08" + formatBytes(f.size) + "\uff09";
    });

    async function readSseClassifyResponse(res, setProgress) {
      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += value;
        let sep;
        while ((sep = buffer.indexOf("\n\n")) !== -1) {
          const chunk = buffer.slice(0, sep);
          buffer = buffer.slice(sep + 2);
          for (const line of chunk.split("\n")) {
            if (line.startsWith("data: ")) {
              const payload = JSON.parse(line.slice(6));
              if (payload.type === "progress") {
                setProgress(payload.pct, payload.message || "");
              } else if (payload.type === "error") {
                const err = new Error(payload.detail || "\u8bf7\u6c42\u5931\u8d25");
                err.status = payload.status;
                throw err;
              } else if (payload.type === "result") {
                return payload.data;
              }
            }
          }
        }
      }
      throw new Error("\u672a\u6536\u5230\u5b8c\u6574\u7ed3\u679c");
    }

'''

new_submit = r'''    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.getElementById("file");
      const f = input.files[0];
      if (!f) return;

      const progressWrap = document.getElementById("progress-wrap");
      const progressBar = document.getElementById("progress-bar-inner");
      const progressLabel = document.getElementById("progress-label");
      const submitBtn = document.getElementById("submit-btn");

      function setProgress(pct, msg) {
        progressWrap.hidden = false;
        const p = Math.max(0, Math.min(100, Number(pct) || 0));
        progressBar.style.width = p + "%";
        progressBar.parentElement.setAttribute("aria-valuenow", String(Math.round(p)));
        progressLabel.textContent = (msg || "") + " \u00b7 " + Math.round(p) + "%";
      }

      function hideProgress() {
        progressWrap.hidden = true;
        progressBar.style.width = "0%";
        progressLabel.textContent = "";
      }

      statusEl.textContent = "";
      summaryCard.hidden = true;
      resultCard.hidden = true;
      gridBody.innerHTML = "";

      const fd = new FormData();
      fd.append("file", f);
      const fws = selectedFrameworks();
      if (fws.length) {
        fd.append("frameworks", JSON.stringify(fws));
      }
      if (aiEnhanceCb && aiEnhanceCb.checked) {
        fd.append("ai_enhance", "true");
      }
      fd.append("stream_progress", "true");

      submitBtn.disabled = true;
      hideProgress();
      try {
        const clsUrl = new URL("api/classify", apiRootUrl());
        const res = await fetch(clsUrl.href, {
          method: "POST",
          body: fd,
          credentials: "same-origin",
        });

        let data;
        const ct = (res.headers.get("content-type") || "").toLowerCase();
        if (!res.ok) {
          hideProgress();
          try {
            data = await res.json();
          } catch (_) {
            data = {};
          }
          const det = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || "");
          statusEl.textContent = det || ("\u8bf7\u6c42\u5931\u8d25 HTTP " + res.status);
          return;
        }

        if (ct.includes("text/event-stream")) {
          data = await readSseClassifyResponse(res, setProgress);
          setProgress(100, "\u5b8c\u6210");
        } else {
          data = await res.json();
        }
        hideProgress();

        const af = (data.applied_frameworks || []).join(", ");
        const afNote = af ? "\uff08\u6807\u51c6\uff1a" + af + "\uff09" : "";
        let stMsg = "\u5b8c\u6210\uff1a\u5171 " + data.fields.length + " \u4e2a\u5b57\u6bb5" + afNote;
        if (data.ai_enhancement_applied) {
          stMsg += " \u00b7 AI \u5df2\u589e\u5f3a";
          if (data.ai_model) stMsg += "\uff08" + data.ai_model + "\uff09";
        }
        statusEl.textContent = stMsg;

        const sums = data.summary || {};
        summaryEl.innerHTML = Object.keys(sums)
          .sort((a, b) => Number(b) - Number(a))
          .map((k) => {
            return (
              '<span class="chip ' +
              levelClass(k) +
              '">\u7b49\u7ea7 ' +
              k +
              "\uff1a" +
              sums[k] +
              "</span>"
            );
          })
          .join("");
        summaryCard.hidden = false;

        for (const row of data.fields) {
          const fld = row.field;
          const tr = document.createElement("tr");
          const tags = (row.tags || []).join(", ");
          const rationale = row.rationale || "";
          let aiCell = "\u2014";
          if (row.ai) {
            if (row.ai.review_suggested) {
              aiCell =
                '<span class="badge-warn" title="\u5efa\u8bae\u4eba\u5de5\u590d\u6838">\u590d\u6838</span>';
            } else {
              aiCell =
                '<span class="badge-ai" title="\u5df2\u7528\u5916\u90e8\u6a21\u578b\u8c03\u6574">\u589e\u5f3a</span>';
            }
            if (row.ai.baseline_level != null && row.ai.baseline_level !== row.level) {
              aiCell +=
                ' <small style="opacity:.85">\u539f' +
                row.ai.baseline_level +
                "\u2192" +
                row.level +
                "</small>";
            }
          }
          tr.innerHTML = `
            <td><span class="badge ${levelClass(row.level)}">${row.level}</span></td>
            <td>${escapeHtml(fld.database)}</td>
            <td>${escapeHtml(fld.schema ?? fld.schema_name)}</td>
            <td>${escapeHtml(fld.table)}</td>
            <td><code>${escapeHtml(fld.column)}</code></td>
            <td>${escapeHtml(fld.data_type)}</td>
            <td>${escapeHtml(fld.comment)}</td>
            <td>${escapeHtml(tags)}</td>
            <td>${aiCell}</td>
            <td class="rationale">${escapeHtml(rationale)}</td>`;
          gridBody.appendChild(tr);
        }
        resultCard.hidden = false;
      } catch (err) {
        hideProgress();
        statusEl.textContent = err.message || "\u7f51\u7edc\u6216\u89e3\u6790\u9519\u8bef";
        console.error(err);
      } finally {
        submitBtn.disabled = false;
      }
    });
'''

t = t[:idx] + helpers + new_submit + t[end_pos:]
html.write_text(t, encoding="utf-8", newline="\n")

c = css.read_text(encoding="utf-8")
append = """

.file-feedback {
  margin: 0.35rem 0 0;
  font-size: 0.88rem;
  color: var(--muted);
}

.progress-wrap {
  width: 100%;
  margin: 0.75rem 0 0.5rem;
}

.progress-bar-outer {
  height: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar-inner {
  height: 100%;
  width: 0%;
  background: var(--accent);
  border-radius: 999px;
  transition: width 0.25s ease-out;
}

.progress-label {
  margin: 0.4rem 0 0;
  font-size: 0.85rem;
  color: var(--muted);
  line-height: 1.35;
}
"""
if ".progress-wrap" not in c:
    c = c.rstrip() + append + "\n"
    css.write_text(c, encoding="utf-8", newline="\n")

print("ok")
