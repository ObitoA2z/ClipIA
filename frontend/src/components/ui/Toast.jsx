import { Toaster } from "react-hot-toast";

function ToastHost() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 3500,
        style: {
          background: "#12122a",
          color: "#f8fafc",
          border: "1px solid rgba(99,102,241,0.35)",
        },
      }}
    />
  );
}

export default ToastHost;
