import { isSupabaseConfigured, supabase } from "../lib/supabase";

export async function getAuthHeaders() {
  if (!isSupabaseConfigured || !supabase) {
    return {};
  }
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) {
    return {};
  }
  return { Authorization: `Bearer ${token}` };
}