import { apiRequest } from "./api";

export const loginUser = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const data = await apiRequest("/auth/login", "POST", formData, true);

  localStorage.setItem("token", data.access_token);

  return data;
};

export const registerUser = async ({ email, password, company, plan }) => {
  const data = await apiRequest("/auth/register", "POST", {
    email,
    password,
    company: company || null,
    plan: plan || null,
  });

  localStorage.setItem("token", data.access_token);

  return data;
};