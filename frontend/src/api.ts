import WebApp from '@twa-dev/sdk';

// Automatically points to the relative path when containerized with Nginx mapping, or falls back to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getUserId = () => {
    // Safely extract the ID, providing a testing fallback when run outside of Telegram
    if (WebApp.initDataUnsafe && WebApp.initDataUnsafe.user) {
        return WebApp.initDataUnsafe.user.id;
    }
    console.warn("Telegram WebApp user context not found. Using fallback ID.");
    return 123456789;
};

export const fetchUser = async () => {
    const res = await fetch(`${API_BASE_URL}/users/${getUserId()}`);
    if (!res.ok) throw new Error('Failed to fetch user');
    return res.json();
};

export const updateLanguage = async (lang: string) => {
    const res = await fetch(`${API_BASE_URL}/users/${getUserId()}/language`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: lang })
    });
    return res.json();
};

export const submitRelease = async (formData: FormData) => {
    formData.append('tg_id', getUserId().toString());
    const res = await fetch(`${API_BASE_URL}/releases`, {
        method: 'POST',
        body: formData
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to submit release');
    }
    return res.json();
};

export const submitReceipt = async (file: File, amount: number) => {
    const formData = new FormData();
    formData.append('tg_id', getUserId().toString());
    formData.append('amount', amount.toString());
    formData.append('receipt', file);

    const res = await fetch(`${API_BASE_URL}/transactions/receipt`, {
        method: 'POST',
        body: formData
    });
    if (!res.ok) throw new Error('Failed to submit receipt');
    return res.json();
};