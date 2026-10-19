import type React from "react";
import { Outlet } from "react-router-dom";
import { useUser } from "./contexts/user/UserContext";

const ProtectedRoute: React.FC = () => {
  const { user, logout, loading } = useUser();

  if (loading) return <div>Loading...</div>;

  if (!user) logout();

  return <Outlet />;
};

export default ProtectedRoute;
