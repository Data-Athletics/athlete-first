import { createContext, useContext } from "react";
import type { User, UserLogin, UserSignUp, UserUpdate } from "../../types/User";

export interface UserContextType {
  user: User | null;
  loading: boolean;
  getMe: () => Promise<void>;
  login: (userLogin: UserLogin) => Promise<void>;
  signup: (userSignUp: UserSignUp) => Promise<void>;
  updateMe: (userUpdate: UserUpdate) => Promise<User>;
  logout: () => void;
}

export const UserContext = createContext<UserContextType | null>(null);

export function useUser() {
  const context = useContext(UserContext);

  if (!context) {
    throw new Error("useUser must be used within UserProvider");
  }

  return context;
}
