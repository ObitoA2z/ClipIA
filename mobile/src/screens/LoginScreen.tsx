import React, { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { login } from "../services/api";

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Erreur", "Email et mot de passe requis");
      return;
    }
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigation.navigate("MainTabs");
    } catch (error: any) {
      Alert.alert("Erreur", error?.response?.data?.detail || "Connexion impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connexion</Text>
      <Text style={styles.sub}>Authentification mobile ClipAI.</Text>

      <TextInput
        style={styles.input}
        placeholder="Email"
        placeholderTextColor="#7C7CA5"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        style={styles.input}
        placeholder="Mot de passe"
        placeholderTextColor="#7C7CA5"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Pressable style={[styles.button, loading && styles.buttonDisabled]} onPress={handleLogin} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? "Connexion..." : "Se connecter"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#080812", padding: 20, justifyContent: "center", gap: 12 },
  title: { color: "#F8FAFC", fontSize: 30, fontWeight: "800" },
  sub: { color: "#94A3B8", marginBottom: 8 },
  input: {
    backgroundColor: "#0A0A1E",
    borderWidth: 1,
    borderColor: "#32327A",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: "#F8FAFC",
  },
  button: { backgroundColor: "#6366F1", borderRadius: 12, alignItems: "center", paddingVertical: 12 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "white", fontWeight: "700" },
});
