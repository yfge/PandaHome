import { getRequestConfig } from 'next-intl/server';

export default getRequestConfig(async ({ locale }) => {
  if (!locale) throw new Error('Locale is required');
  return {
    messages: (await import(`./locales/${locale}.json`)).default,
    locale
  };
}); 