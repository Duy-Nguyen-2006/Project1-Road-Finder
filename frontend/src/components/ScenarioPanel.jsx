import { useState } from "react";
import PropTypes from "prop-types";
import { useUserData } from "../hooks/useUserData";

export default function ScenarioPanel({
  user,
  scenarioSnapshot,
  onLoadScenario,
  onAddPresetShipper,
}) {
  const {
    scenarios,
    presets,
    loading,
    error,
    saveScenario,
    deleteScenario,
    savePreset,
    deletePreset,
  } = useUserData(user);

  const [scenarioName, setScenarioName] = useState("");
  const [presetName, setPresetName] = useState("");
  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(false);

  if (!user) {
    return (
      <div className="panel-card auth-gate-card">
        <h2>Đăng nhập để dùng VRP</h2>
        <p className="helper-text">
          Tính năng tối ưu quãng đường yêu cầu đăng nhập Google. Bấm &quot;Đăng nhập Google&quot; ở góc trên.
        </p>
      </div>
    );
  }

  const handleSaveScenario = async () => {
    setActionError(null);
    setBusy(true);
    try {
      await saveScenario(scenarioName, scenarioSnapshot());
      setScenarioName("");
    } catch (err) {
      setActionError(err?.message ?? "Không lưu được kịch bản.");
    } finally {
      setBusy(false);
    }
  };

  const handleSavePreset = async () => {
    const shipper = scenarioSnapshot().shippers?.[0];
    if (!shipper) {
      setActionError("Thêm ít nhất một shipper trước khi lưu preset.");
      return;
    }
    setActionError(null);
    setBusy(true);
    try {
      await savePreset({
        name: presetName,
        latitude: shipper.location.latitude,
        longitude: shipper.location.longitude,
      });
      setPresetName("");
    } catch (err) {
      setActionError(err?.message ?? "Không lưu được preset.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel-card scenario-panel">
      <h2>Kịch bản & preset</h2>
      <p className="helper-text">Lưu/tải đơn, shipper và lựa chọn hiện tại.</p>

      <div className="scenario-form">
        <input
          type="text"
          placeholder="Tên kịch bản mới"
          value={scenarioName}
          onChange={(event) => setScenarioName(event.target.value)}
          disabled={busy}
        />
        <button
          className="secondary-button"
          type="button"
          onClick={handleSaveScenario}
          disabled={busy || !scenarioName.trim()}
        >
          Lưu kịch bản
        </button>
      </div>

      <div className="scenario-form">
        <input
          type="text"
          placeholder="Tên shipper preset (shipper đầu tiên)"
          value={presetName}
          onChange={(event) => setPresetName(event.target.value)}
          disabled={busy}
        />
        <button
          className="secondary-button"
          type="button"
          onClick={handleSavePreset}
          disabled={busy || !presetName.trim()}
        >
          Lưu preset
        </button>
      </div>

      {(error || actionError) && (
        <p className="error-text">{actionError ?? error}</p>
      )}

      {loading ? (
        <p className="helper-text">Đang tải dữ liệu…</p>
      ) : (
        <>
          <h3>Kịch bản đã lưu</h3>
          {scenarios.length === 0 ? (
            <p className="empty-text">Chưa có kịch bản nào.</p>
          ) : (
            <ul className="scenario-list">
              {scenarios.map((item) => (
                <li key={item.id} className="scenario-list-item">
                  <button
                    className="link-button"
                    type="button"
                    onClick={() => onLoadScenario(item.payload)}
                  >
                    {item.name}
                  </button>
                  <button
                    className="icon-button"
                    type="button"
                    aria-label={`Xóa ${item.name}`}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await deleteScenario(item.id);
                      } catch (err) {
                        setActionError(err?.message ?? "Không xóa được.");
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}

          <h3>Shipper preset</h3>
          {presets.length === 0 ? (
            <p className="empty-text">Chưa có preset nào.</p>
          ) : (
            <ul className="scenario-list">
              {presets.map((item) => (
                <li key={item.id} className="scenario-list-item">
                  <button
                    className="link-button"
                    type="button"
                    onClick={() =>
                      onAddPresetShipper({
                        latitude: item.latitude,
                        longitude: item.longitude,
                      })
                    }
                  >
                    {item.name}
                  </button>
                  <button
                    className="icon-button"
                    type="button"
                    aria-label={`Xóa ${item.name}`}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await deletePreset(item.id);
                      } catch (err) {
                        setActionError(err?.message ?? "Không xóa được.");
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}

ScenarioPanel.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.string,
    email: PropTypes.string,
  }),
  scenarioSnapshot: PropTypes.func.isRequired,
  onLoadScenario: PropTypes.func.isRequired,
  onAddPresetShipper: PropTypes.func.isRequired,
};