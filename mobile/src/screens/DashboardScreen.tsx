import React, { useEffect, useState } from "react";
import { Alert, ScrollView, StyleSheet } from "react-native";

import ProcessingStatus from "../components/ProcessingStatus";
import VideoInput from "../components/VideoInput";
import { getVideoStatus, processVideo } from "../services/api";

export default function DashboardScreen() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentVideoId, setCurrentVideoId] = useState("");

  useEffect(() => {
    if (!currentVideoId) {
      return;
    }
    const timer = setInterval(async () => {
      try {
        const status = await getVideoStatus(currentVideoId);
        setProgress(Number(status?.progress_percent || 0));
        if (status?.status === "done") {
          clearInterval(timer);
          Alert.alert("Succes", "Tes clips sont prets.");
        }
        if (status?.status === "error") {
          clearInterval(timer);
          Alert.alert("Erreur", status?.error_message || "Erreur pipeline");
        }
      } catch (error: any) {
        clearInterval(timer);
        Alert.alert("Erreur", error?.response?.data?.detail || "Impossible de verifier le statut");
      }
    }, 5000);

    return () => clearInterval(timer);
  }, [currentVideoId]);

  const submit = async () => {
    if (!url.trim()) {
      return;
    }
    setLoading(true);
    try {
      const result = await processVideo(url.trim());
      setCurrentVideoId(result.video_id || result.id || "");
      setProgress(Number(result.progress_percent || 0));
      Alert.alert("Pipeline lance", "Le traitement est en cours.");
    } catch (error: any) {
      Alert.alert("Erreur", error?.response?.data?.detail || "Lancement impossible");
    } finally {
      setLoading(false);
    }
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
  content: { padding: 16, gap: 16 },
});
