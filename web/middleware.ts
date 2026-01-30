import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  // 支持的语言列表
  locales: ['en', 'zh'],
  // 默认语言
  defaultLocale: 'zh'
});

export const config = {
  // 匹配所有路径除了 api, _next, 静态文件等
  matcher: ['/((?!api|_next|.*\\..*).*)']
};
