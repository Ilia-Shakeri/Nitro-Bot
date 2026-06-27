export interface User {
  telegram_id: number;
  language_preference: string;
  credits: number;
}

export interface Transaction {
  id: number;
  amount: number;
  status: string;
  created_at: string;
}

export interface Release {
  id: number;
  song_name: string;
  artist_name: string;
  status: string;
  cover_url: string;
  created_at: string;
}
