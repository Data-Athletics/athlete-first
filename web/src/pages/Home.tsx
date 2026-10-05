import type React from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Nav from "../Nav";
import "./Home.css";

const Home: React.FC = () => {
  const navigate = useNavigate();

  const [signingUp, setSigningUp] = useState(false);

  const onGoClick = () => {
    console.log("Authing");
    navigate("/dashboard");
  };

  return (
    <>
      <Nav />
      <div className="home-container">
        <div className="login-container">
          <h1 className="page-header login-header">Welcome to AthleteFirst</h1>
          <div className="button-container">
            <button
              className={`login-button ${signingUp || "button-selected"}`}
              onClick={() => setSigningUp(false)}
            >
              Log In
            </button>
            <button
              className={`login-button ${signingUp && "button-selected"}`}
              onClick={() => setSigningUp(true)}
            >
              Sign Up
            </button>
          </div>
          <h3 className="input-title">Username</h3>
          <input className="login-input" />
          <h3 className="input-title">Password</h3>
          <input className="login-input" />
          {signingUp && (
            <>
              <h3 className="input-title">Height</h3>
              <input className="login-input" />
              <h3 className="input-title">Weight</h3>
              <input className="login-input" />
              <h3 className="input-title">Sex</h3>
              <input className="login-input" />
              <h3 className="input-title">Age</h3>
              <input className="login-input" />
            </>
          )}
          <button className="login-button" onClick={onGoClick}>
            Go
          </button>
        </div>
        <h2 className="home-catch">Consent and Privacy for Athletes!!</h2>
      </div>
    </>
  );
};

export default Home;
