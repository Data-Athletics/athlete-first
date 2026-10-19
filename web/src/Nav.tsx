import { useNavigate } from "react-router-dom";
import "./Nav.css";

interface NavProps {
  children?: React.ReactNode;
}

const Nav = ({ children }: NavProps) => {
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
        {children}
      </div>
    </>
  );
};

export default Nav;
