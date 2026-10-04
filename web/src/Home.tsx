import "./Home.css";

function Home() {
  return (
    <>
      <div className="home-container">
        <div className="login-container">
          <h1 className="login-header">Welcome to AthleteFirst</h1>
          <div className="button-container">
            <button className="login-button">Log In</button>
            <button className="login-button">Sign Up</button>
          </div>
          <h3 className="input-title">Username</h3>
          <input className="login-input" />
          <h3 className="input-title">Password</h3>
          <input className="login-input" />
          <button className="login-button" style={{"alignSelf": "flex-end"}}>Go</button>
        </div>
        <h2 className="home-catch">Consent and Privacy for Athletes!!</h2>
      </div>
    </>
  );
}

export default Home;
