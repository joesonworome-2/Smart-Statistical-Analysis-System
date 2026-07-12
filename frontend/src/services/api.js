import { auth } from "../firebase";

const API_URL = "http://localhost:8000/api";

export const uploadDataset = async (file) => {
  const token = await auth.currentUser.getIdToken();

  const formData = new FormData();
  formData.append("dataset", file);

  const response = await fetch(`${API_URL}/datasets/upload/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  return response.json();
};