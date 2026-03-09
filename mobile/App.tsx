import React from "react";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import AppNavigator from "./src/navigation/AppNavigator";

const queryClient = new QueryClient();

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: "#080812",
    card: "#12122A",
    text: "#F8FAFC",
    border: "#2A2A4A",
    primary: "#6366F1"
  }
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer theme={theme}>
        <AppNavigator />
      </NavigationContainer>
    </QueryClientProvider>
  );
}
