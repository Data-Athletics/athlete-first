import type React from "react";
import Nav from "../Nav";
import "./Dashboard.css";

const Dashboard: React.FC = () => {
  return (
    <>
      <Nav>
        <div className="nav-button-container">
          <button>Player A</button>
          <button>Team A</button>
        </div>
      </Nav>
      <div className="dashboard-container">
        <div className="title-container">
          <h1 className="page-header">Metrics</h1>
          <button style={{ marginLeft: "auto" }}>Upload</button>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
