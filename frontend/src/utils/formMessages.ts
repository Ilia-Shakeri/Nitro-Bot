type Lang = 'en' | 'fa';

const messages: Record<Lang, Record<string, string>> = {
  en: {
    'Unknown error': 'Unknown error',
    'Error sending ticket': 'Error sending ticket',
    'Subject and message are required': 'Subject and message are required',
    'Please fill all required fields.': 'Please fill all required fields.',
    'Amount must be greater than zero': 'Amount must be greater than zero',
    'Exchange rate unavailable': 'Exchange rate unavailable',
  },
  fa: {
    'Unknown error': 'خطای نامشخص',
    'Error sending ticket': 'ارسال تیکت ناموفق بود',
    'Subject and message are required': 'موضوع و پیام الزامی هستند',
    'Please fill all required fields.': 'لطفا همه فیلدهای ضروری را پر کنید.',
    'Amount must be greater than zero': 'مبلغ باید بیشتر از صفر باشد',
    'Exchange rate unavailable': 'نرخ تبدیل در دسترس نیست',
  },
};

export const formMessage = (message: string | undefined, lang: string, fallback = 'Unknown error') => {
  const table = lang.startsWith('fa') ? messages.fa : messages.en;
  if (!message) return table[fallback] ?? message ?? fallback;
  if (message.startsWith('Not enough credits')) {
    return lang.startsWith('fa') ? 'اعتبار کافی نیست' : message;
  }
  return table[message] ?? message;
};
