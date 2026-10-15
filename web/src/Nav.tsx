import { useNavigate } from "react-router-dom";
import "./Nav.css";

const Nav = () => {
  const navigate = useNavigate();

  const onTitleClick = () => {
    console.log("Back Home!");
    navigate("/");
  };

  return (
    <>
      <div className="nav-container">
        <h1 className="title-header" onClick={onTitleClick}>
          AthleteFirst
        </h1>
      </div>
    </>
  );
};

export default Nav;
