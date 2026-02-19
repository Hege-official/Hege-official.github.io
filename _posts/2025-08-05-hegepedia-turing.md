---
# 页面基本信息
title: "艾伦·图灵"
excerpt: "艾伦·麦席森·图灵是一位英国数学家、逻辑学家，他被广泛认为是理论计算机科学和人工智能的奠基人。"
date: 2023-10-27

# 维基百科风格的配置
# ----------------------------------------------------

# 1. 开启右侧目录 (Table of Contents)
toc: true
toc_label: "目录"
toc_icon: "bars" # Font Awesome icon

# 2. Infobox (右侧信息框) 数据
#    这是你为 infobox.html 提供数据的地方
infobox_header: "艾伦·图灵"
infobox_image: "/assets/images/alan-turing.jpg" # 确保图片存在于此路径
infobox_caption: "图灵约摄于1951年"
infobox_data:
  - label: "全名"
    value: "艾伦·麦席森·图灵<br>(Alan Mathison Turing)"
  - label: "出生"
    value: "1912年6月23日<br>英国伦敦"
  - label: "逝世"
    value: "1954年6月7日（41岁）<br>英国柴郡"
  - label: "研究领域"
    value: "数学、逻辑学、密码学、计算机科学"
  - label: "著名成就"
    value: "图灵机、图灵测试、破解恩尼格玛密码机"
  - label: "荣誉"
    value: "大英帝国勋章 (OBE)"
---

{% comment %} 
  将 infobox include 放在文章开头，这样它会浮动在右侧 
{% endcomment %}

{% include infobox.html %}

**艾伦·麦席森·图灵**（Alan Mathison Turing，1912年6月23日—1954年6月7日），是一位英国数学家、逻辑学家，他被广泛认为是理论计算机科学和人工智能的奠基人。[^1] 他的工作对现代计算机的发展产生了深远影响。

在第二次世界大战期间，图灵在布莱切利园（Bletchley Park）的政府密码学校工作，领导了破解德国恩尼格玛密码机的团队。这一成就被认为大大缩短了战争的进程，拯救了数百万人的生命。[^2]

## 早期生活与教育

图灵出生于伦敦的梅达韦尔。他的父亲是英属印度公务员。图灵在谢伯恩学校就读，并于1931年前往剑桥大学国王学院学习数学。

{% include figure image_path="/assets/images/turing-statue.jpg" alt="图灵雕像" caption="位于曼彻斯特的图灵雕像。" %}

## 职业生涯

{% include embed_box.html
  title="关键贡献"
  icon="star"
  content="
- **理论层面**: 奠定了可计算性理论的基础。
- **实践层面**: 破解恩尼格玛密码机，极大地帮助了盟军。
- **思想层面**: 提出了人工智能的哲学问题（图灵测试）。
" %}

### 图灵机
1936年，图灵发表了论文《论可计算数及其在判定问题上的应用》，提出了"图灵机"的抽象计算模型，为通用计算机的诞生奠定了理论基础。

{% include embed_box.html
  title="图灵机核心概念"
  icon="cogs"
  content="
图灵机不是一个实体机器，而是一个抽象的数学模型。它包含：

1.  **一条无限长的纸带** (Tape)
2.  **一个读写头** (Head)
3.  **一个状态寄存器** (State Register)
4.  **一套有限的指令集** (Action Table)
" %}

### 人工智能
战后，他在国家物理实验室工作，设计了自动计算机（ACE）。他后来提出的“图灵测试”至今仍是衡量机器智能的重要标准。

## 个人生活与逝世

由于当时的法律，图灵因其同性恋行为而受到刑事起诉。1954年，他因氰化物中毒去世，官方裁定为自杀，但也有人对死因提出质疑。

<div class="notice--info">
  <h4>后续平反</h4>
  2009年，英国政府为当年对图灵的不公对待正式道歉。2013年，女王伊丽莎白二世对他予以皇家赦免。
</div>

## 另见
- [图灵测试](https://zh.wikipedia.org/wiki/图灵测试)
- [恩尼格玛密码机](https://zh.wikipedia.org/wiki/恩尼格玛密码机)

## 外部链接
- [Andrew Hodges 的图灵官方网站](http://www.turing.org.uk/turing/)
- [斯坦福哲学百科全书上的“艾伦·图灵”词条](https://plato.stanford.edu/entries/turing/)

## 模板使用说明
Front Matter (头部信息区):

toc: true: 这是 Minimal Mistakes 的内置功能，开启后会自动在右侧生成目录。
infobox_header, infobox_image, infobox_caption, infobox_data: 这些是你为自定义 infobox.html 提供的所有数据。infobox_data 是一个列表，每一项都有 label 和 value。你可以在 value 中使用 <br> 进行换行。
{% include infobox.html %}: 将这行代码放在正文的最前面，它会自动读取 Front Matter 的数据并生成信息框。

脚注/参考文献 \[^1]:

在需要引用的地方使用 \[^1]、\[^2] 等。
在文章末尾，使用 \[^1]: 参考文献的具体内容 来定义脚注。
为了美观，我建议在文末创建一个“参考文献”章节，并在其下方列出所有脚注定义。（注意：Markdown 会自动将所有脚注渲染在文章最末尾，但将定义写在参考文献章节下有助于组织你的源文件。）
图片 {% include figure %}: 使用 Minimal Mistakes 的 figure include 可以方便地插入带标题的图片，比原生 Markdown ![]() 更强大。

提示框 .notice--info: Minimal Mistakes 内置了多种提示框样式，如 .notice, .notice--info, .notice--warning, .notice--success, .notice--danger 等。你只需用 <div> 或其他 HTML 标签包裹内容并添加相应的 class 即可。


## 参考文献
[^1]: Copeland, B. Jack. "Alan Turing: The building of a legend." *The Turing Guide*, 2017.
[^2]: Hodges, Andrew. *Alan Turing: The Enigma*. Princeton University Press, 2012.