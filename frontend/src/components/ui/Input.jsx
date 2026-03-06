function Input({ label, id, className = "", ...props }) {
  return (
    <label htmlFor={id} style={{ display: "grid", gap: 8 }}>
      {label ? <span className="muted">{label}</span> : null}
      <input id={id} className={["ui-input", className].filter(Boolean).join(" ")} {...props} />
    </label>
  );
}

export default Input;
