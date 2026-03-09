import React, { useState } from "react";
import { ScrollView, StyleSheet } from "react-native";

import ProcessingStatus from "../components/ProcessingStatus";
import VideoInput from "../components/VideoInput";

export default function DashboardScreen() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress] = useState(35);

  const submit = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1200);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <VideoInput value={url} onChange={setUrl} onSubmit={submit} loading={loading} />
      <ProcessingStatus progress={progress} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#080812" },
  content: { padding: 16, gap: 16 }
});
