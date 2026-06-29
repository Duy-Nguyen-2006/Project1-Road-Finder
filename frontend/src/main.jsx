import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "leaflet/dist/leaflet.css";
import "./App.css";
import App from "./App";
import AuthCallback from "./pages/AuthCallback";

const queryClient = new QueryClient();
const isAuthCallback = window.location.pathname === "/auth/callback";
const RootComponent = isAuthCallback ? AuthCallback : App;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RootComponent />
    </QueryClientProvider>
  </React.StrictMode>
);
