import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { processVideo } from "../../services/api";

const initialState = {
  videoUrl: '',
  videoId: '',
  videoTitle: '',
  processing: false,
  processed: false,
  error: null,
}

export const processVideoThunk = createAsyncThunk(
  "video/processVideo",
  async (url, thunkAPI) => {
    try {
      const data = await processVideo(url);
      return data;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data?.detail || "Failed to process video"
      );
    }
  }
);

const videoSlice = createSlice({
  name: 'video',
  initialState,

  reducers: {
    setVideoUrl: (state, action) => {
      state.videoUrl = action.payload
    },

    setVideoId: (state, action) => {
      state.videoId = action.payload
    },

    setVideoTitle: (state, action) => {
      state.videoTitle = action.payload
    },

    setProcessing: (state, action) => {
      state.processing = action.payload
    },

    setProcessed: (state, action) => {
      state.processed = action.payload
    },

    setVideoError: (state, action) => {
      state.error = action.payload
    },

    resetVideo: () => initialState,
  },
  
  extraReducers: (builder) => {
  builder
    .addCase(processVideoThunk.pending, (state) => {
      state.processing = true;
      state.processed = false;
      state.error = null;
    })
    .addCase(processVideoThunk.fulfilled, (state, action) => {
      state.processing = false;
      state.processed = true;
      state.videoId = action.payload.video_id;
      state.error = null;
    })
    .addCase(processVideoThunk.rejected, (state, action) => {
      state.processing = false;
      state.processed = false;
      state.error = action.payload;
    });
},
})

export const {
  setVideoUrl,
  setVideoId,
  setVideoTitle,
  setProcessing,
  setProcessed,
  setVideoError,
  resetVideo,
} = videoSlice.actions

export default videoSlice.reducer