import React from "react";
import { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { View, Text, Pressable, StyleSheet } from "react-native";

export default function BottomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  return (
    <View style={styles.container}>
      {state.routes.map((route, index) => {
        const isFocused = state.index === index;
        const label = descriptors[route.key].options.tabBarLabel ?? descriptors[route.key].options.title ?? route.name;
        return (
          <Pressable
            key={route.key}
            style={styles.item}
            onPress={() => navigation.navigate(route.name as never)}
          >
            <Text style={[styles.label, isFocused && styles.labelActive]}>{String(label)}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "#0D0D1F",
    borderTopWidth: 1,
    borderTopColor: "#2A2A4A",
    paddingBottom: 8,
    paddingTop: 8
  },
  item: { flex: 1, alignItems: "center", justifyContent: "center", minHeight: 44 },
  label: { color: "#8E8EB5", fontWeight: "600", fontSize: 12 },
  labelActive: { color: "#6366F1" }
});
