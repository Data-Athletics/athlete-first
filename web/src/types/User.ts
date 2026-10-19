export type UserSex = "male" | "female";

export interface UserLogin {
  username: string;
  password: string;
}

export interface UserLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserSignUp extends UserLogin {
  height: number | null;
  weight: number | null;
  sex: UserSex | null;
  age: number | null;
}

export interface User extends Omit<UserSignUp, "password"> {
  id: number;
  can_login: boolean;
  is_active: boolean;
}

export interface UserUpdate extends Partial<Omit<User, "id" | "can_login">> {}
