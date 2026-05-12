import { apiRequest } from "./api";

export const getUsers = async () => {
  return await apiRequest("/users");
};