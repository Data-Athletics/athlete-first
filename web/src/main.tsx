import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, Outlet, RouterProvider } from "react-router-dom";
import { UserProvider } from "./contexts/user/UserProvider.tsx";
import Dashboard from "./pages/Dashboard.tsx";
import Home from "./pages/Home.tsx";
import Profile from "./pages/Profile.tsx";
import ProtectedRoute from "./ProtectedRoute.tsx";
import "./styles/button.css";
import "./styles/index.css";
import "./styles/input.css";

const router = createBrowserRouter([
  {
    element: (
      <UserProvider>
        <Outlet />
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
