/*
 * 中文检索分词器 / CJK tokenizer for lunr
 *
 * lunr 自带的 tokenizer 按空格与连字符切词，中文没有词间空格，整段中文会被
 * 当成一个 token，导致「搜索不准」。这里用「CJK 单字 + 相邻二元组」的方式切词：
 *
 *   索引：连续中文段 -> 所有单字 + 所有相邻二字组合（如 艺宫市 -> 艺 宫 市 艺宫 宫市）
 *   查询：连续中文段长度 >= 2 时只用二元组（精确），单字时用单字
 *   西文：按非字母数字切分为单词
 *
 * 索引与查询共用同一套规则，保证命中一致。挂到 window.HegeSearch，供 lunr-zh.js 使用。
 */
(function () {
  "use strict";

  // CJK 统一表意文字（基本区、扩展 A、兼容区）——这些字符没有词间空格
  var CJK = /[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/;
  // 西文单词里保留的字符：拉丁字母（含常见重音）与数字
  var WORD_KEEP = /[^0-9a-z\u00c0-\u024f]+/g;

  function isCJK(ch) {
    return CJK.test(ch);
  }

  function flushWord(tokens, word) {
    if (!word) return;
    var parts = word.split(WORD_KEEP);
    for (var p = 0; p < parts.length; p++) {
      if (parts[p]) tokens.push(parts[p]);
    }
  }

  // 索引分词：单字 + 相邻二元组
  function tokenize(input) {
    if (input == null) return [];
    var str = input.toString().toLowerCase();
    var tokens = [];
    var cjkRun = "";
    var word = "";

    function flushCJK() {
      if (!cjkRun) return;
      var n = cjkRun.length;
      for (var i = 0; i < n; i++) tokens.push(cjkRun.charAt(i));
      for (var j = 0; j + 1 < n; j++) tokens.push(cjkRun.substr(j, 2));
      cjkRun = "";
    }

    for (var k = 0; k < str.length; k++) {
      var ch = str.charAt(k);
      if (isCJK(ch)) {
        flushWord(tokens, word);
        word = "";
        cjkRun += ch;
      } else {
        flushCJK();
        word += ch;
      }
    }
    flushWord(tokens, word);
    flushCJK();

    return tokens;
  }

  // 查询分词：CJK 二元组优先，单字回退；西文同索引
  function queryTerms(input) {
    if (input == null) return [];
    var str = input.toString().toLowerCase();
    var tokens = [];
    var cjkRun = "";
    var word = "";

    function flushCJK() {
      if (!cjkRun) return;
      var n = cjkRun.length;
      if (n === 1) {
        tokens.push(cjkRun);
      } else {
        for (var j = 0; j + 1 < n; j++) tokens.push(cjkRun.substr(j, 2));
      }
      cjkRun = "";
    }

    for (var k = 0; k < str.length; k++) {
      var ch = str.charAt(k);
      if (isCJK(ch)) {
        flushWord(tokens, word);
        word = "";
        cjkRun += ch;
      } else {
        flushCJK();
        word += ch;
      }
    }
    flushWord(tokens, word);
    flushCJK();

    return tokens;
  }

  window.HegeSearch = {
    tokenize: tokenize,
    queryTerms: queryTerms,
    isCJK: isCJK
  };
})();
