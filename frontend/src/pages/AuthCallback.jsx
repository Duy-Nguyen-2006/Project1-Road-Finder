import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

export default function AuthCallback() {
  const [message, setMessage] = useState("Đang xử lý đăng nhập…");

  useEffect(() => {
    if (!supabase) {
      setMessage("Supabase chưa được cấu hình.");
      return undefined;
    }

    let mounted = true;

    async function finishAuth() {
      const params = new URLSearchParams(globalThis.location.search);
      const code = params.get("code");
      const authError = params.get("error_description") ?? params.get("error");

      if (authError) {
        if (mounted) setMessage(authError);
        return;
      }

      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (!mounted) return;
        if (error) {
          setMessage(error.message);
          return;
        }
        globalThis.location.replace("/");
        return;
      }

      const { data, error } = await supabase.auth.getSession();
      if (!mounted) return;
      if (error) {
        setMessage(error.message);
        return;
      }
      if (data.session) {
        globalThis.location.replace("/");
        return;
      }

      setMessage("Không lấy được phiên đăng nhập. Thử đăng nhập lại.");
    }

    finishAuth();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="auth-callback">
      <p>{message}</p>
    </div>
  );
}