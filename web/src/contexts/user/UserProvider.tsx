import axios from "axios";
import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { api, TOKEN_KEY } from "../../api/axios";
import type {
  User,
  UserLogin,
  UserLoginResponse,
  UserSignUp,
  UserUpdate,
} from "../../types/User";
import { UserContext } from "./UserContext";

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  const getMe = async () => {
    if (!localStorage.getItem(TOKEN_KEY)) {
      logout();
      return;
    }

    try {
      const { data } = await api.get<User>("/user/me");
      setUser(data);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        logout();
      } else {
        console.log("Failed to get current user:", error);
      }
    }
  };

  const login = async (userLogin: UserLogin) => {
    setLoading(true);
    const { data } = await api.post<UserLoginResponse>(
      "/auth/token",
      new URLSearchParams({
        username: userLogin.username,
        password: userLogin.password,
      }),
    );
    localStorage.setItem(TOKEN_KEY, data.access_token);
    await getMe();
    setLoading(false);
  };

  const signup = async (userSignUp: UserSignUp) => {
    setLoading(true);
    const { data: signup_data } = await api.post<User>("auth/register", {
      username: userSignUp.username,
      password: userSignUp.password,
    });
    await login({
      username: signup_data.username,
      password: userSignUp.password,
    });
    const user_data = await updateMe({
      height: userSignUp.height,
      weight: userSignUp.weight,
      age: userSignUp.age,
      sex: userSignUp.sex,
    });
    setUser(user_data);
    setLoading(false);
  };

  const updateMe = async (updateUser: UserUpdate): Promise<User> => {
    const { data } = await api.patch<User>("user/me", updateUser);
    console.log(data);
    setUser(data);
    return data;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    navigate("/");
  };

  useEffect(() => {
    setLoading(true);
    void (async () => {
      try {
        if (localStorage.getItem(TOKEN_KEY)) {
          await getMe();
        }
      } catch (error) {
        console.error("Failed to restore session:", error);
      }
      setLoading(false);
    })();
  }, []);

  return (
    <UserContext.Provider
      value={{
        user,
        loading,
        getMe,
        login,
        signup,
        updateMe: updateMe,
        logout,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}
