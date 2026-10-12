import type React from "react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import "./Dashboard.css";

const Dashboard: React.FC = () => {
  const { user, logout } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    console.log(user);
  }, [user]);

  return (
    <>
      <Nav>
        <div className="nav-button-container">
          <button>Player A</button>
          <button>Team A</button>
          <button onClick={() => navigate("/profile")}>Profile</button>
          <button onClick={logout}>Log out</button>
        </div>
      </Nav>
      <div className="page-container">
        <div className="title-container">
          <h1 className="page-header">Metrics</h1>
          <button style={{ marginLeft: "auto" }}>Upload</button>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
