import type React from "react";
import type { User } from "../types/User";
import "./Player.css";

interface PlayerProps {
  player: User;
}

const Player: React.FC<PlayerProps> = (props) => {
  return (
    <>
      <div className="player-container">
        <div className="title-container">
          <h3 className="input-title">{props.player.username}</h3>
        </div>
      </div>
    </>
  );
};

export default Player;
