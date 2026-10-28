import type React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useUser } from "./contexts/user/UserContext";

const ProtectedRoute: React.FC = () => {
  const { user, loading } = useUser();

  if (loading) return <div>Loading...</div>;

  if (!user) return <Navigate to="/" replace />;

  return <Outlet />;
};

export default ProtectedRoute;
