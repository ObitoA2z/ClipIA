import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function LoginScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connexion</Text>
      <Text style={styles.sub}>Authentification mobile ClipAI.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#080812", padding: 20, justifyContent: "center" },
  title: { color: "#F8FAFC", fontSize: 30, fontWeight: "800" },
  sub: { color: "#94A3B8", marginTop: 8 }
});
