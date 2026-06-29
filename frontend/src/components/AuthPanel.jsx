import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

export default function AuthPanel() {
  const { configured, loading, user, signInWithGoogle, signOut } = useAuth();
  const [error, setError] = useState(null);

  if (!configured) {
    return (
      <div className="auth-panel auth-panel--disabled">
        <span className="helper-text">Auth: chưa cấu hình Supabase env</span>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="auth-panel">
        <span className="helper-text">Đang tải phiên…</span>
      </div>
    );
  }

  if (user) {
    const label = user.user_metadata?.full_name || user.user_metadata?.name || user.email;
    return (
      <div className="auth-panel auth-panel--signed-in">
        <span className="auth-user" title={user.email}>
          {label}
        </span>
        <button className="secondary-button auth-button" type="button" onClick={() => signOut()}>
          Đăng xuất
        </button>
      </div>
    );
  }

  return (
    <div className="auth-panel">
      <button
        className="primary-button auth-button"
        type="button"
        onClick={async () => {
          setError(null);
          try {
            await signInWithGoogle();
          } catch (err) {
            setError(err?.message ?? "Không đăng nhập được.");
          }
        }}
      >
        Đăng nhập Google
      </button>
      {error ? <p className="error-text auth-error">{error}</p> : null}
    </div>
  );
}