import React from "react";
import PropTypes from "prop-types";

const ROAD_TYPES = [
  { value: "highway", label: "Đường cao tốc" },
  { value: "residential", label: "Đường dân cư" },
  { value: "tertiary", label: "Đường nhỏ" },
];

export default function OptionsPanel({ avoidRoadTypes, onAvoidRoadTypesChange }) {
  const toggleRoadType = (type) => {
    if (avoidRoadTypes.includes(type)) {
      onAvoidRoadTypesChange(avoidRoadTypes.filter((t) => t !== type));
    } else {
      onAvoidRoadTypesChange([...avoidRoadTypes, type]);
    }
  };

  return (
    <div className="panel-card">
      <h2>Tùy chọn</h2>
      <div className="options-panel">
        {ROAD_TYPES.map(({ value, label }) => (
          <label key={value}>
            <input
              type="checkbox"
              checked={avoidRoadTypes.includes(value)}
              onChange={() => toggleRoadType(value)}
            />
            Tránh {label}
          </label>
        ))}
      </div>
    </div>
  );
}

OptionsPanel.propTypes = {
  avoidRoadTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
  onAvoidRoadTypesChange: PropTypes.func.isRequired,
};
