import Spinner from "./Spinner";

function Button({
  children,
  type = "button",
  variant = "primary",
  className = "",
  loading = false,
  disabled = false,
  ...props
}) {
  const classes = [`ui-btn`, `ui-btn-${variant}`, className].filter(Boolean).join(" ");

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...props}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
        {loading ? <Spinner size={16} /> : null}
        {children}
      </span>
    </button>
  );
}

export default Button;
