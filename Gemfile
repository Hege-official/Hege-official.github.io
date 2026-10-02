# 本地默认使用国内镜像；CI 通过 GEM_SOURCE 覆盖为 rubygems.org，
# 因为 GitHub runner 访问 gems.ruby-china.com 会出现 TLS 握手失败。
source ENV.fetch("GEM_SOURCE", "https://gems.ruby-china.com/")

group :jekyll_plugins do
  gem "jekyll-include-cache"
  gem "minimal-mistakes-jekyll", "~> 4.24.0"
  gem 'jekyll-sitemap', '~> 1.4'
end
gem "tzinfo", "~> 2.0"
gem "tzinfo-data", "~> 1.2025"
