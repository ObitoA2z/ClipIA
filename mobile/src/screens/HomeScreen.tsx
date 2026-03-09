import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>ClipAI Mobile</Text>
      <Text style={styles.subtitle}>Transforme tes videos longues en shorts en quelques minutes.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#080812", padding: 20, justifyContent: "center" },
  title: { color: "#F8FAFC", fontSize: 32, fontWeight: "800" },
  subtitle: { color: "#94A3B8", marginTop: 12, fontSize: 16 }
});
