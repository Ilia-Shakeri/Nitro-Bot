export interface User {
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  language_preference: string;
  credits: number;
  referral_points: number;
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
  title_key: string;
  title_params: Record<string, string | number>;
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

export type ArtistRole = 'primary' | 'featured';

export interface ReleaseArtist {
  name: string;
  role: ArtistRole;
}

export interface Release {
  id: number;
  song_name: string;
  artist_name: string;
  artists: ReleaseArtist[];
  producers: string | null;
  legal_name: string;
  legal_names: string[];
  release_date: string;
  is_rerelease: boolean;
  original_release_date: string | null;
  genre: string | null;
  sub_genre: string | null;
  mapping_spotify: string | null;
  mapping_apple: string | null;
  profile_email: string | null;
  requires_new_profile: boolean;
  status: string;
  cover_url: string;
  is_edit: boolean;
  copyright_requested: boolean;
  charged_cost: number;
  refunded_at: string | null;
  created_at: string;
}

export interface Pricing {
  nitro_usd_price_cents: number;
  original_release_price: number;
  discounted_release_price: number;
  copyright_price: number;
  edit_release_price: number;
  minimum_topup_nitro: number;
}

export interface PaymentMethod {
  network?: string | null;
  address?: string | null;
  number?: string | null;
  holder?: string | null;
}

export interface PaymentConfig {
  card: PaymentMethod | null;
  usdt: PaymentMethod | null;
}
