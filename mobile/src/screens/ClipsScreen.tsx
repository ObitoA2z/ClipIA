import React from "react";
import { FlatList, StyleSheet, View } from "react-native";

import ClipCard from "../components/ClipCard";

const MOCK_CLIPS = [
  { id: "1", title: "Hook ultra viral", duration: 42.5 },
  { id: "2", title: "Moment fort emotion", duration: 55.2 },
  { id: "3", title: "Tip concret en 30 secondes", duration: 33.4 }
];

export default function ClipsScreen() {
  return (
    <View style={styles.container}>
      <FlatList
        data={MOCK_CLIPS}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.content}
        renderItem={({ item }) => <ClipCard title={item.title} duration={item.duration} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#080812" },
  content: { padding: 16, gap: 14 }
});
