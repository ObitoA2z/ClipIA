import React from "react";
import { View, Text, TextInput, Pressable, StyleSheet } from "react-native";

export default function VideoInput({ value, onChange, onSubmit, loading }: { value: string; onChange: (value: string) => void; onSubmit: () => void; loading: boolean; }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Coller un lien YouTube</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder="https://www.youtube.com/watch?v=..."
        placeholderTextColor="#7C7CA5"
        style={styles.input}
      />
      <Pressable style={[styles.button, loading && styles.buttonDisabled]} onPress={onSubmit} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? "Traitement..." : "Generer mes clips"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: "#12122A", borderRadius: 18, padding: 16, borderWidth: 1, borderColor: "#2A2A4A", gap: 12 },
  title: { color: "#F8FAFC", fontSize: 18, fontWeight: "700" },
  input: { backgroundColor: "#0A0A1E", borderWidth: 1, borderColor: "#32327A", borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10, color: "#F8FAFC" },
  button: { backgroundColor: "#6366F1", borderRadius: 12, alignItems: "center", paddingVertical: 12 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "white", fontWeight: "700" }
});
