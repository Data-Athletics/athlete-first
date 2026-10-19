import type React from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import { alertUser } from "../utils/alerts";
import "./Home.css";
import "./Profile.css";

const Profile: React.FC = () => {
  const { user, updateMe: updateUser, logout } = useUser();

  const navigate = useNavigate();
  const [height, setHeight] = useState(user?.height ?? 0);
  const [weight, setWeight] = useState(user?.weight ?? 0);
  const [sex, setSex] = useState<string>(user?.sex ?? "");
  const [age, setAge] = useState(user?.age ?? 0);

  const [updating, setUpdating] = useState(false);

  const onUpdateClick = async () => {
    setUpdating(true);
    const loweredSex = sex.toLowerCase();
    if (loweredSex === "male" || loweredSex === "female") {
      await updateUser({
        height,
        weight,
        sex: loweredSex,
        age,
      });
      alertUser("Update Successful!");
    } else {
      alertUser("Sex must be either 'male' or 'female'");
    }
    setUpdating(false);
  };

  useEffect(() => {
    if (!user) return;

    setHeight(user.height ?? 0);
    setWeight(user.weight ?? 0);
    setAge(user.age ?? 0);
    setSex(user.sex ?? "");
  }, [user]);

  return (
    <>
      <Nav>
        <div className="nav-button-container">
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={logout}>Log out</button>
        </div>
      </Nav>
      <div className="page-container">
        <div className="title-container">
          <h1 className="page-header">Profile</h1>
        </div>
        <div className="fields-container">
          <h3 className="input-title">Height</h3>
          <input
            className="login-input"
            type="number"
            placeholder="Height"
            value={height}
            onChange={(e) => setHeight(Number(e.target.value))}
            required
          />
          <h3 className="input-title">Weight</h3>
          <input
            className="login-input"
            type="number"
            placeholder="Weight"
            value={weight}
            onChange={(e) => setWeight(Number(e.target.value))}
            required
          />
          <h3 className="input-title">Sex</h3>
          <input
            className="login-input"
            type="text"
            placeholder="Sex"
            value={sex}
            onChange={(e) => setSex(e.target.value)}
            required
          />
          <h3 className="input-title">Age</h3>
          <input
            className="login-input"
            type="number"
            placeholder="Age"
            value={age}
            onChange={(e) => setAge(Number(e.target.value))}
            required
          />
          <button className="login-button" onClick={onUpdateClick}>
            {updating ? "Updating..." : "Update"}
          </button>
        </div>
      </div>
    </>
  );
};

export default Profile;
