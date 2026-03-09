import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function VideoDetailScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Detail video</Text>
      <Text style={styles.sub}>Preview, clips et metadonnees video.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#080812", padding: 20 },
  title: { color: "#F8FAFC", fontSize: 24, fontWeight: "700" },
  sub: { color: "#94A3B8", marginTop: 8 }
});
