function Card({ as: Tag = "section", className = "", children, ...props }) {
  return (
    <Tag className={["ui-card", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </Tag>
  );
}

export default Card;
