import type React from "react";
import { useNavigate } from "react-router-dom";
import { useTeam } from "../contexts/team/TeamContext";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import "./Requests.css";

const Requests: React.FC = () => {
  const navigate = useNavigate();

  const { user, logout } = useUser();
  const { teamsOptions } = useTeam();

  return (
    <>
      <Nav>
        <div className="nav-button-container">
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/profile")}>Profile</button>
          <button onClick={logout}>Log out</button>
        </div>
      </Nav>
      <div className="page-container">
        <div className="title-container">
          <h1 className="page-header">Requests</h1>
        </div>
      </div>
    </>
  );
};

export default Requests;
