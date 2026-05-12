import { apiRequest } from "./api";

export const getTransactions = async () => {
  return await apiRequest("/transactions/");
};

export const getTransactionStats = async () => {
  return await apiRequest("/transactions/stats");
};

export const createTransaction = async (transaction) => {
  return await apiRequest("/transactions", "POST", transaction);
};