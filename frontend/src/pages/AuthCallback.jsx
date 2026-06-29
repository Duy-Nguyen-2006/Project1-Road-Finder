import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

export default function AuthCallback() {
  const [message, setMessage] = useState("Đang xử lý đăng nhập…");

  useEffect(() => {
    if (!supabase) {
      setMessage("Supabase chưa được cấu hình.");
      return;
    }

    supabase.auth.getSession().then(({ data, error }) => {
      if (error) {
        setMessage(error.message);
        return;
      }
      if (data.session) {
        window.location.replace("/");
        return;
      }
      setMessage("Không lấy được phiên đăng nhập. Thử đăng nhập lại.");
    });
  }, []);

  return (
    <div className="auth-callback">
      <p>{message}</p>
    </div>
  );
}