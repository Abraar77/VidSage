import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Process YouTube video
export const processVideo = async (url) => {
  const response = await API.post("/api/video/process", {
    url,
    language: "en",
  });

  return response.data;
};

// Ask questions about the video
export const askQuestion = async (video_id, question, conversation_id = null) => {
  const response = await API.post("/api/chat/ask", {
    video_id,
    question,
    conversation_id
  });

  return response.data;
};

// Fetch all conversations for the sidebar
export const getConversations = async () => {
  const response = await API.get("/api/chat/conversations");
  return response.data;
};

// Fetch messages from a selected conversation
export const getConversationMessages = async (conversationId) => {
  const response = await API.get(
    `/api/chat/conversations/${conversationId}`
  );
  return response.data;
};

export default API;