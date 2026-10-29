---
layout: none
---

/*
 * 中文站内搜索（lunr + CJK 二元组分词）
 *
 * 依赖：lunr.min.js、lunr-store.js（var store）、lunr-cjk.js（window.HegeSearch）
 * 与默认的 lunr-en.js 相比：
 *   - 索引与查询改为中文二元组分词，中文关键词可正常命中
 *   - 标题/分类/标签加权，正文参与但不喧宾夺主
 *   - 结果摘要按字符截断并定位到关键词附近，避免中文被 split(" ") 挤成一段
 */

var idx = lunr(function () {
  this.ref("id");
  this.field("title", { boost: 10 });
  this.field("categories", { boost: 4 });
  this.field("tags", { boost: 4 });
  this.field("excerpt");

  this.pipeline.remove(lunr.trimmer);

  for (var item in store) {
    var doc = store[item];
    this.add({
      title: HegeSearch.tokenize(doc.title),
      categories: HegeSearch.tokenize(asText(doc.categories)),
      tags: HegeSearch.tokenize(asText(doc.tags)),
      excerpt: HegeSearch.tokenize(doc.excerpt),
      id: item
    });
  }
});

function asText(value) {
  if (!value) return "";
  if (Object.prototype.toString.call(value) === "[object Array]") {
    return value.join(" ");
  }
  return value.toString();
}

function escapeHtml(value) {
  return asText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// 在已转义的文本里安全地包 <mark>，避免关键词里的 < & 破坏标记
function highlight(escaped, terms) {
  var out = escaped;
  for (var i = 0; i < terms.length; i++) {
    var t = escapeHtml(terms[i]);
    if (!t) continue;
    var re = new RegExp(t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g");
    out = out.replace(re, function (m) { return "\u0000" + m + "\u0001"; });
  }
  return out.replace(/\u0000/g, "<mark>").replace(/\u0001/g, "</mark>");
}

// 以关键词为中心截取摘要（中文无空格，不能按词截断）
function makeSnippet(text, terms, max) {
  var content = asText(text).replace(/\s+/g, " ").trim();
  max = max || 120;
  if (!content) return "";

  var at = -1;
  for (var i = 0; i < terms.length; i++) {
    var pos = content.indexOf(terms[i]);
    if (pos >= 0 && (at < 0 || pos < at)) at = pos;
  }

  var start = at > 30 ? at - 30 : 0;
  var snippet = content.slice(start, start + max);
  return (start > 0 ? "…" : "") +
    highlight(escapeHtml(snippet), terms) +
    (start + max < content.length ? "…" : "");
}

// 本脚本由 scripts.html 以普通 <script> 同步注入，而 jQuery 所在的
// main.min.js 是 defer 加载——脚本执行时 $ 可能还不存在。这里不依赖 jQuery，
// 等 DOM 就绪后直接绑定，避免 "ReferenceError: $ is not defined" 让搜索整体失效。
function onSearchReady(fn) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fn);
  } else {
    fn();
  }
}

onSearchReady(function () {
  // 搜索页的输入框在 _layouts/search.html 的 .archive 里，普通页面则在
  // search/search_form.html 的 .search-content 里，取文档中唯一那个。
  var input = document.getElementById("search");
  var resultdiv = document.getElementById("results");
  if (!input || !resultdiv) return;

  var timer = null;

  input.addEventListener("input", function () {
    var value = input.value;
    var terms = HegeSearch.queryTerms(value);

    if (timer) clearTimeout(timer);
    timer = setTimeout(function () {
      if (!value || !value.replace(/\s/g, "") || !terms.length) {
        resultdiv.innerHTML = "";
        return;
      }

      var result = idx.query(function (q) {
        terms.forEach(function (term) {
          // REQUIRED：各查询片段都要命中（AND）。默认 OPTIONAL 是 OR 语义，
          // 一个二元组撞上就能返回结果，"不存在的词啊" 也会因为 "在的" 命中而误报。
          q.term(term, { boost: 100, presence: lunr.Query.presence.REQUIRED });
          // 西文补一个前缀通配，缓解词形差异；中文二元组无需通配
          if (!HegeSearch.isCJK(term.charAt(0))) {
            q.term(term, {
              usePipeline: false,
              wildcard: lunr.Query.wildcard.TRAILING,
              boost: 10
            });
          }
        });
      });

      var label = (result.length === 0)
        ? "没有找到与「" + value.trim() + "」相关的记录"
        : "找到 " + result.length + " 条相关记录";

      var html = '<p class="results__found">' + escapeHtml(label) + "</p>";

      for (var i = 0; i < result.length; i++) {
        var ref = result[i].ref;
        var doc = store[ref];
        if (!doc) continue;

        var meta = [];
        var cats = asText(doc.categories);
        if (cats) meta.push('<span class="results__tag">' + escapeHtml(cats) + "</span>");
        if (doc.date) meta.push('<time class="results__date">' + escapeHtml(doc.date.slice(0, 10)) + "</time>");

        html +=
          '<div class="list__item">' +
            '<article class="archive__item results__item" itemscope itemtype="https://schema.org/CreativeWork">' +
              '<div class="results__meta">' + meta.join('<span class="results__sep">·</span>') + "</div>" +
              '<h2 class="archive__item-title" itemprop="headline">' +
                '<a href="' + escapeHtml(doc.url) + '" rel="permalink">' +
                  highlight(escapeHtml(doc.title), terms) +
                "</a>" +
              "</h2>" +
              '<p class="archive__item-excerpt" itemprop="description">' +
                makeSnippet(doc.excerpt, terms) +
              "</p>" +
            "</article>" +
          "</div>";
      }

      if (result.length === 0) {
        html +=
          '<div class="results__empty">' +
            "<p>请换一个关键词试试，例如机构名、地名或法规名称。</p>" +
          "</div>";
      }

      resultdiv.innerHTML = html;
    }, 120);
  });
});
