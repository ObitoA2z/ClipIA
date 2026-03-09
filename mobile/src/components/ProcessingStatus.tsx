import React from "react";
import { View, Text, StyleSheet } from "react-native";

const steps = ["Telechargement", "Extraction audio", "Transcription", "Analyse IA", "Decoupe", "Formatage", "Pret"];

export default function ProcessingStatus({ progress = 0 }: { progress: number }) {
  const activeIndex = Math.min(steps.length - 1, Math.floor((progress / 100) * steps.length));
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Traitement en cours</Text>
      <View style={styles.progressTrack}>
        <View style={[styles.progressBar, { width: `${progress}%` }]} />
      </View>
      {steps.map((step, index) => (
        <Text key={step} style={[styles.step, index <= activeIndex && styles.stepActive]}>
          {index <= activeIndex ? "?" : "?"} {step}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: "#12122A", borderRadius: 18, padding: 16, borderWidth: 1, borderColor: "#2A2A4A", gap: 8 },
  title: { color: "#F8FAFC", fontSize: 16, fontWeight: "700" },
  progressTrack: { height: 10, borderRadius: 999, backgroundColor: "#1A1A3A", overflow: "hidden" },
  progressBar: { height: "100%", backgroundColor: "#6366F1" },
  step: { color: "#8E8EB5", fontSize: 13 },
  stepActive: { color: "#F8FAFC" }
});
