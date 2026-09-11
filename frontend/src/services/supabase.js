import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://epgibdkihcswaaresftw.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVwZ2liZGtpaGNzd2FhcmVzZnR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwNjMxOTcsImV4cCI6MjEwNDYzOTE5N30.echJzPzlM0UYhLjZ__TW7ldf_o52CFHDNtPfqhpMovU';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
