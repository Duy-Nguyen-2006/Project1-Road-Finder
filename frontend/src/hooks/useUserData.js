import { useCallback, useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

export function useUserData(user) {
  const [scenarios, setScenarios] = useState([]);
  const [presets, setPresets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!user || !supabase) {
      setScenarios([]);
      setPresets([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [scenarioResult, presetResult] = await Promise.all([
        supabase
          .from("saved_scenarios")
          .select("id, name, payload, updated_at")
          .order("updated_at", { ascending: false }),
        supabase
          .from("shipper_presets")
          .select("id, name, latitude, longitude, created_at")
          .order("created_at", { ascending: false }),
      ]);

      if (scenarioResult.error) throw scenarioResult.error;
      if (presetResult.error) throw presetResult.error;

      setScenarios(scenarioResult.data ?? []);
      setPresets(presetResult.data ?? []);
    } catch (err) {
      setError(err?.message ?? "Không tải được dữ liệu người dùng.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const saveScenario = useCallback(
    async (name, payload) => {
      if (!user || !supabase) {
        throw new Error("Cần đăng nhập để lưu kịch bản.");
      }
      const trimmed = name.trim();
      if (!trimmed) {
        throw new Error("Tên kịch bản không được để trống.");
      }

      const { data, error: insertError } = await supabase
        .from("saved_scenarios")
        .insert({ name: trimmed, payload, user_id: user.id })
        .select("id, name, payload, updated_at")
        .single();

      if (insertError) throw insertError;
      setScenarios((prev) => [data, ...prev]);
      return data;
    },
    [user]
  );

  const deleteScenario = useCallback(
    async (scenarioId) => {
      if (!user || !supabase) return;
      const { error: deleteError } = await supabase
        .from("saved_scenarios")
        .delete()
        .eq("id", scenarioId);
      if (deleteError) throw deleteError;
      setScenarios((prev) => prev.filter((item) => item.id !== scenarioId));
    },
    [user]
  );

  const savePreset = useCallback(
    async ({ name, latitude, longitude }) => {
      if (!user || !supabase) {
        throw new Error("Cần đăng nhập để lưu shipper preset.");
      }
      const trimmed = name.trim();
      if (!trimmed) {
        throw new Error("Tên preset không được để trống.");
      }

      const { data, error: insertError } = await supabase
        .from("shipper_presets")
        .insert({
          name: trimmed,
          latitude,
          longitude,
          user_id: user.id,
        })
        .select("id, name, latitude, longitude, created_at")
        .single();

      if (insertError) throw insertError;
      setPresets((prev) => [data, ...prev]);
      return data;
    },
    [user]
  );

  const deletePreset = useCallback(
    async (presetId) => {
      if (!user || !supabase) return;
      const { error: deleteError } = await supabase
        .from("shipper_presets")
        .delete()
        .eq("id", presetId);
      if (deleteError) throw deleteError;
      setPresets((prev) => prev.filter((item) => item.id !== presetId));
    },
    [user]
  );

  return {
    scenarios,
    presets,
    loading,
    error,
    refresh,
    saveScenario,
    deleteScenario,
    savePreset,
    deletePreset,
  };
}