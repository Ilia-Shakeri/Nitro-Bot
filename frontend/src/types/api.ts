export interface User {
  telegram_id: number;
  language_preference: string;
  credits: number;
}

export interface Transaction {
  id: number;
  amount: number;
  status: string;
  payment_method: string;
  created_at: string;
}

export interface LedgerEntry {
  id: string;
  amount: number;
  direction: 'credit' | 'debit';
  title: string;
  status: string;
  created_at: string;
}

export interface SupportMessage {
  id: number;
  sender: 'user' | 'admin';
  message: string;
  created_at: string;
}

export interface SupportTicket {
  id: number;
  subject: string;
  status: string;
  created_at: string;
  messages: SupportMessage[];
}

export interface Release {
  id: number;
  song_name: string;
  artist_name: string;
  genre: string | null;
  status: string;
  failure_reason?: string | null;
  cover_url: string;
  is_edit: boolean;
  copyright_requested: boolean;
  created_at: string;
}
