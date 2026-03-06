function Spinner({ size = 18 }) {
  return (
    <span
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        border: "2px solid rgba(248, 250, 252, 0.2)",
        borderTopColor: "#f8fafc",
        display: "inline-block",
        animation: "spin 0.9s linear infinite",
      }}
    />
  );
}

export default Spinner;
