---
title: "文章归档"
layout: archive
permalink: /archive/
---

{% assign posts_by_year = site.posts | group_by_exp: "post", "post.date | date: '%Y'" %}
{% if posts_by_year.size > 0 %}
{% for year in posts_by_year %}
<h2 class="archive__subtitle">{{ year.name }}</h2>
{% for post in year.items %}
{% include archive-single.html %}
{% endfor %}
{% endfor %}
{% else %}
<p>暂无文章</p>
{% endif %}
