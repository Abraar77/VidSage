
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { askQuestion,getConversations,getConversationMessages } from "../../services/api";

const initialState = {
  messages: [],
  conversationId: null,
  loading: false,
  error: null,
  conversations: [],
  historyLoading: false,
  selectedConversationLoading: false,
};

export const askQuestionThunk = createAsyncThunk(
  "chat/askQuestion",
  async ({ videoId, question }, thunkAPI) => {
    try {
      // Get the existing conversation ID from Redux
      const conversationId = thunkAPI.getState().chat.conversationId;

      // Send it along with the question
      const data = await askQuestion(
        videoId,
        question,
        conversationId
      );

      return data;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data?.detail || "Failed to get AI response"
      );
    }
  }
);
// Fetch all conversations
export const fetchConversationsThunk = createAsyncThunk(
  "chat/fetchConversations",
  async (_, thunkAPI) => {
    try {
      return await getConversations();
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data?.detail || error.message
      );
    }
  }
);

// Fetch messages from a selected conversation
export const fetchConversationMessagesThunk = createAsyncThunk(
  "chat/fetchConversationMessages",
  async (conversationId, thunkAPI) => {
    try {
      return await getConversationMessages(conversationId);
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data?.detail || error.message
      );
    }
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState,

  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },

    clearMessages: (state) => {
      state.messages = [];
      state.conversationId = null;
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(askQuestionThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })

      .addCase(askQuestionThunk.fulfilled, (state, action) => {
        state.loading = false;

        // Remember the conversation ID returned by backend
        state.conversationId = action.payload.conversation_id;

        state.messages.push({
          role: "assistant",
          content: action.payload.answer,
        });
      })

      .addCase(askQuestionThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      
                  // Fetch conversation history
      .addCase(fetchConversationsThunk.pending, (state) => {
        state.historyLoading = true;
        state.error = null;
      })
      .addCase(fetchConversationsThunk.fulfilled, (state, action) => {
        state.historyLoading = false;
        state.conversations = action.payload;
      })
      .addCase(fetchConversationsThunk.rejected, (state, action) => {
        state.historyLoading = false;
        state.error = action.payload;
      })

      // Fetch selected conversation messages
      .addCase(fetchConversationMessagesThunk.pending, (state) => {
        state.selectedConversationLoading = true;
        state.error = null;
      })
      .addCase(fetchConversationMessagesThunk.fulfilled, (state, action) => {
        state.selectedConversationLoading = false;
        state.conversationId = action.payload.conversation_id;
        state.messages = action.payload.messages.map((message) => ({
          role: message.role,
          content: message.content,
        }));
      })
      .addCase(fetchConversationMessagesThunk.rejected, (state, action) => {
        state.selectedConversationLoading = false;
        state.error = action.payload;
      })
      
  },
});

export const { addMessage, clearMessages } = chatSlice.actions;

export default chatSlice.reducer;
