import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';

export default getRequestConfig(async ({ locale }) => {
  // 验证语言设置
  if (!locale || !['zh', 'en'].includes(locale)) {
    notFound();
  }

  const messages = (await import(`./locales/${locale}.json`)).default;

  return {
    messages,
    timeZone: 'Asia/Shanghai',
    now: new Date(),
    locale
  };
}); 