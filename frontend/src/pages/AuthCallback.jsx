import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

const RETRY_LABEL = "Thử đăng nhập lại";

function readAuthParams() {
  const search = new URLSearchParams(globalThis.location?.search ?? "");
  const hashString = globalThis.location?.hash?.replace(/^#/, "") ?? "";
  const hash = new URLSearchParams(hashString);

  const code = search.get("code") ?? hash.get("code");
  const accessToken =
    hash.get("access_token") ?? search.get("access_token");
  const refreshToken =
    hash.get("refresh_token") ?? search.get("refresh_token");
  const errorDescription =
    search.get("error_description") ??
    hash.get("error_description") ??
    search.get("error") ??
    hash.get("error");

  return { code, accessToken, refreshToken, errorDescription };
}

export default function AuthCallback() {
  const [message, setMessage] = useState("Đang xử lý đăng nhập…");
  const [canRetry, setCanRetry] = useState(false);

  useEffect(() => {
    if (!supabase) {
      setMessage("Supabase chưa được cấu hình.");
      setCanRetry(true);
      return undefined;
    }

    let mounted = true;

    async function finishAuth() {
      const { code, accessToken, refreshToken, errorDescription } =
        readAuthParams();

      if (errorDescription) {
        console.error("[auth] OAuth returned an error:", errorDescription);
        if (mounted) {
          setMessage(`Đăng nhập thất bại: ${errorDescription}. ${RETRY_LABEL}.`);
          setCanRetry(true);
        }
        return;
      }

      if (code) {
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);
        if (!mounted) return;
        if (error) {
          console.error("[auth] exchangeCodeForSession failed:", error);
          setMessage(`Không đổi được mã đăng nhập: ${error.message}. ${RETRY_LABEL}.`);
          setCanRetry(true);
          return;
        }
        if (data?.session) {
          globalThis.location.replace("/");
          return;
        }
      } else if (accessToken && refreshToken) {
        const { data, error } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        });
        if (!mounted) return;
        if (error) {
          console.error("[auth] setSession failed:", error);
          setMessage(`Không khôi phục được phiên: ${error.message}. ${RETRY_LABEL}.`);
          setCanRetry(true);
          return;
        }
        if (data?.session) {
          globalThis.location.replace("/");
          return;
        }
      }

      const { data: sessionData, error: sessionError } =
        await supabase.auth.getSession();
      if (!mounted) return;
      if (sessionError) {
        console.error("[auth] getSession failed:", sessionError);
        setMessage(`Không đọc được phiên: ${sessionError.message}. ${RETRY_LABEL}.`);
        setCanRetry(true);
        return;
      }
      if (sessionData?.session) {
        globalThis.location.replace("/");
        return;
      }

      console.warn(
        "[auth] No code, tokens, or stored session found at /auth/callback",
        { hasCode: Boolean(code), hasTokens: Boolean(accessToken && refreshToken) }
      );
      setMessage(
        "Không lấy được phiên đăng nhập. Hãy thử đăng nhập lại bằng nút bên dưới."
      );
      setCanRetry(true);
    }

    finishAuth();
    return () => {
      mounted = false;
    };
  }, []);

  function handleRetry() {
    globalThis.location.replace("/");
  }

  return (
    <div className="auth-callback">
      <p>{message}</p>
      {canRetry ? (
        <button
          className="primary-button"
          type="button"
          onClick={handleRetry}
        >
          {RETRY_LABEL}
        </button>
      ) : null}
    </div>
  );
}
