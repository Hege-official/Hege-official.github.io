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

// 以关键词为中心截取摘要（中文无空格，不能按词截断）
function makeSnippet(text, terms) {
  var content = asText(text);
  var max = 110;
  if (!content) return "";
  if (content.length <= max) return escapeHtml(content);

  var at = -1;
  for (var i = 0; i < terms.length; i++) {
    var pos = content.indexOf(terms[i]);
    if (pos >= 0 && (at < 0 || pos < at)) at = pos;
  }

  var start = at > 40 ? at - 40 : 0;
  var snippet = content.slice(start, start + max);
  return (start > 0 ? "…" : "") + escapeHtml(snippet) + (start + max < content.length ? "…" : "");
}

$(document).ready(function () {
  var $input = $("input#search");
  if (!$input.length) return;

  var timer = null;

  $input.on("keyup", function () {
    var value = $(this).val();
    var terms = HegeSearch.queryTerms(value);
    var resultdiv = $("#results");

    if (timer) clearTimeout(timer);
    timer = setTimeout(function () {
      if (!value || !value.replace(/\s/g, "") || !terms.length) {
        resultdiv.empty();
        return;
      }

      var result = idx.query(function (q) {
        terms.forEach(function (term) {
          q.term(term, { boost: 100 });
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
        ? "没有找到匹配记录"
        : result.length + " 条记录匹配";

      var html = '<p class="results__found">' + escapeHtml(label) + "</p>";

      for (var i = 0; i < result.length; i++) {
        var ref = result[i].ref;
        var doc = store[ref];
        if (!doc) continue;

        var teaser = doc.teaser
          ? '<div class="archive__item-teaser"><img src="' + escapeHtml(doc.teaser) +
            '" alt="" loading="lazy" decoding="async"></div>'
          : "";

        html +=
          '<div class="list__item">' +
            '<article class="archive__item" itemscope itemtype="https://schema.org/CreativeWork">' +
              '<h2 class="archive__item-title" itemprop="headline">' +
                '<a href="' + escapeHtml(doc.url) + '" rel="permalink">' + escapeHtml(doc.title) + "</a>" +
              "</h2>" +
              teaser +
              '<p class="archive__item-excerpt" itemprop="description">' +
                makeSnippet(doc.excerpt, terms) +
              "</p>" +
            "</article>" +
          "</div>";
      }

      resultdiv.empty().append(html);
    }, 120);
  });
});
