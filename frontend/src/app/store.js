import { configureStore } from '@reduxjs/toolkit'
import chatReducer from '../features/chat/chatSlice'
import videoReducer from '../features/video/videoSlice'

export const store = configureStore({
  reducer: {
    chat: chatReducer,
    video: videoReducer,
  },
})