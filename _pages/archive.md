---
title: "文章归档"
layout: archive  # 或 layout: single（取决于你的主题配置）
permalink: /archive/
---

{% assign posts = site.posts %}  
<!-- # 获取所有文章 -->

{% if posts.size > 0 %}
  <div class="archive__item">
    {% for post in posts %}
      {% include archive-single.html %}  
      <!-- # 渲染单个文章项 -->
    {% endfor %}
  </div>
{% else %}
  <p>暂无文章</p>
{% endif %}