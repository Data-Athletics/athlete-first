import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, Outlet, RouterProvider } from "react-router-dom";
import { BiometricsProvider } from "./contexts/biometrics/BiometricsProvider.tsx";
import { TeamProvider } from "./contexts/team/TeamProvider.tsx";
import { UserProvider } from "./contexts/user/UserProvider.tsx";
import Dashboard from "./pages/Dashboard.tsx";
import Home from "./pages/Home.tsx";
import Profile from "./pages/Profile.tsx";
import Requests from "./pages/Requests.tsx";
import ProtectedRoute from "./ProtectedRoute.tsx";
import "./styles/button.css";
import "./styles/index.css";
import "./styles/input.css";
import "./styles/metric.css";

const router = createBrowserRouter([
  {
    element: (
      <UserProvider>
        <TeamProvider>
          <BiometricsProvider>
            <Outlet />
          </BiometricsProvider>
        </TeamProvider>
      </UserProvider>
    ),
    children: [
      {
        path: "/",
        element: <Home />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "/profile",
            element: <Profile />,
          },
          {
            path: "/dashboard",
            element: <Dashboard />,
          },
          {
            path: "/requests",
            element: <Requests />,
          },
        ],
      },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
