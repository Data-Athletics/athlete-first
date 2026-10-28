import type React from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import { alertUser } from "../utils/alerts";
import "./Home.css";

const Home: React.FC = () => {
  const { login, signup, loading } = useUser();
  const navigate = useNavigate();

  const [signingUp, setSigningUp] = useState(false);

  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [sex, setSex] = useState("");
  const [age, setAge] = useState("");

  const onGoClick = async () => {
    try {
      if (signingUp) {
        const normalizedSex = sex.trim().toLowerCase();
        await signup({
          username,
          name,
          password,
          height: height.trim() === "" ? null : Number(height),
          weight: weight.trim() === "" ? null : Number(weight),
          sex:
            normalizedSex === "male" || normalizedSex === "female"
              ? normalizedSex
              : null,
          age: age.trim() === "" ? null : Number(age),
        });
      } else {
        await login({ username, password });
      }
      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      alertUser(
        signingUp
          ? "You could not be signed up. Please check your information."
          : "You could not be logged in. Please check your username and password.",
      );
    }
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
          <input
            className="text-input"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <h3 className="input-title">Password</h3>
          <input
            className="text-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {signingUp && (
            <>
              <h3 className="input-title">Name</h3>
              <input
                className="text-input"
                type="text"
                placeholder="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <h3 className="input-title">Height</h3>
              <input
                className="text-input"
                type="text"
                placeholder="Height"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
                required
              />
              <h3 className="input-title">Weight</h3>
              <input
                className="text-input"
                type="text"
                placeholder="Weight"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                required
              />
              <h3 className="input-title">Sex</h3>
              <input
                className="text-input"
                type="text"
                placeholder="Sex"
                value={sex}
                onChange={(e) => setSex(e.target.value)}
                required
              />
              <h3 className="input-title">Age</h3>
              <input
                className="text-input"
                type="text"
                placeholder="Age"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                required
              />
            </>
          )}
          <button
            disabled={loading}
            className="login-button login-submit"
            onClick={onGoClick}
          >
            {loading ? (signingUp ? "Signing up..." : "Logging in...") : "Go"}
          </button>
        </div>
        <h2 className="home-catch">Consent and Privacy for Athletes!!</h2>
      </div>
    </>
  );
};

export default Home;
