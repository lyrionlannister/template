import type { FC } from "react";
import { BrowserRouter } from "react-router";
import { AppRoutes } from "./app-routes";

export const App: FC = () => (
  <BrowserRouter>
    <AppRoutes />
  </BrowserRouter>
);
