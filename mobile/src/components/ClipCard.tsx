import React from "react";
import { View, Text, Image, Pressable, StyleSheet } from "react-native";

export default function ClipCard({ title, duration, thumbnailUrl, onPress }: { title: string; duration: number; thumbnailUrl?: string; onPress?: () => void; }) {
  return (
    <Pressable style={styles.card} onPress={onPress}>
      {thumbnailUrl ? <Image source={{ uri: thumbnailUrl }} style={styles.thumb} /> : <View style={[styles.thumb, styles.thumbFallback]} />}
      <View style={styles.body}>
        <Text style={styles.title} numberOfLines={2}>{title}</Text>
        <Text style={styles.meta}>{duration.toFixed(1)}s</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 16, overflow: "hidden", backgroundColor: "#12122A", borderWidth: 1, borderColor: "#2A2A4A" },
  thumb: { width: "100%", height: 160, backgroundColor: "#1A1A3A" },
  thumbFallback: { alignItems: "center", justifyContent: "center" },
  body: { padding: 12, gap: 4 },
  title: { color: "#F8FAFC", fontWeight: "700" },
  meta: { color: "#94A3B8", fontSize: 12 }
});
