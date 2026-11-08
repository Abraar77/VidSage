
import { useState,useEffect,useRef } from 'react'
import { Menu, X, Plus, Play, MessageSquare } from 'lucide-react'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { useDispatch, useSelector } from 'react-redux'
import { addMessage, clearMessages,
  askQuestionThunk,fetchConversationsThunk,fetchConversationMessagesThunk
 } from './features/chat/chatSlice'
import {
  setVideoUrl,
  setVideoId,
  setProcessed,
  processVideoThunk,
  resetVideo
} from './features/video/videoSlice'

function extractVideoId(url) {
  try {
    const parsedUrl = new URL(url)

    if (parsedUrl.hostname === 'youtu.be') {
      return parsedUrl.pathname.slice(1)
    }

    if (
      parsedUrl.hostname === 'www.youtube.com' ||
      parsedUrl.hostname === 'youtube.com' ||
      parsedUrl.hostname === 'm.youtube.com'
    ) {
      if (parsedUrl.pathname === '/watch') {
        return parsedUrl.searchParams.get('v')
      }

      const match = parsedUrl.pathname.match(
        /^\/(embed|shorts)\/([^/?]+)/
      )

      return match ? match[2] : null
    }

    return null
  } catch {
    return null
  }
}

function App() {
  const [url, setUrl] = useState('')
  const [question, setQuestion] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const chatContainerRef = useRef(null)

  const dispatch = useDispatch()
  
  const conversations = useSelector(
  (state) => state.chat.conversations
);

  const conversationId = useSelector(
    (state) => state.chat.conversationId
  );

  const historyLoading = useSelector(
    (state) => state.chat.historyLoading
  );
  
  const messages = useSelector((state) => state.chat.messages)
  const videoUrl = useSelector((state) => state.video.videoUrl)
  
  const videoId = useSelector((state) => state.video.videoId)
  const processing = useSelector((state) => state.video.processing)
  const processed = useSelector((state) => state.video.processed)
  const videoError = useSelector((state) => state.video.error)

  const loading = useSelector((state) => state.chat.loading)
  const chatError = useSelector((state) => state.chat.error)
  
  
  useEffect(() => {
  dispatch(fetchConversationsThunk());
}, [dispatch]);

useEffect(() => {
  const container = chatContainerRef.current

  if (container) {
    container.scrollTo({
      top: container.scrollHeight,
      behavior: 'smooth'
    })
  }
}, [messages, loading])
  
  const handleNewChat = () => {
    dispatch(clearMessages())
    dispatch(resetVideo())

    setUrl('')
    setQuestion('')
    setSidebarOpen(false)
  }
  
  const handleSelectConversation = async (id) => {
  try {
    const conversation = await dispatch(
      fetchConversationMessagesThunk(id)
    ).unwrap();

    // Restore the video's context
    dispatch(setVideoId(conversation.video_id));

    dispatch(
      setVideoUrl(
        `https://www.youtube.com/watch?v=${conversation.video_id}`
      )
    );

    dispatch(setProcessed(true));

    setQuestion('');
    setSidebarOpen(false);

  } catch (error) {
    console.error('Failed to load conversation:', error);
  }
};

const handleVideoSubmit = async (e) => {
  e.preventDefault()

  const trimmedUrl = url.trim()
  const videoId = extractVideoId(trimmedUrl)

  if (!videoId) {
    alert('Please enter a valid YouTube URL')
    return
  }

  dispatch(setVideoUrl(trimmedUrl))

  try {
    await dispatch(processVideoThunk(trimmedUrl)).unwrap()
    setUrl('')
  } catch (error) {
    console.error('Video processing failed:', error)
  }
}

const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!question.trim()) return;

    if (!processed || !videoId) {
      alert("Please process a YouTube video first.");
      return;
    }

    const currentQuestion = question.trim();

    dispatch(
      addMessage({
        role: "user",
        content: currentQuestion,
      })
    );

    setQuestion("");

    await dispatch(
      askQuestionThunk({
        videoId,
        question: currentQuestion,
      })
    );
    dispatch(fetchConversationsThunk());
  };

  return (
    <div className="min-h-screen w-full bg-[#09090b] text-white flex">

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/70 z-40 md:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:sticky top-0 left-0 z-50
          h-screen w-72 shrink-0
          bg-[#111113] border-r border-zinc-800
          p-5 flex flex-col
          transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}
      >

        {/* Sidebar Header */}
        <div className="flex items-center justify-between mb-10">

          <h1 className="text-xl font-bold">
            <span className="text-red-500">▶</span> YouTube AI
          </h1>

          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-2 rounded-lg hover:bg-zinc-800"
            aria-label="Close sidebar"
          >
            <X size={22} />
          </button>

        </div>

        {/* New Chat */}
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-3 bg-white text-black rounded-xl p-3 font-medium hover:bg-zinc-200 transition"
        >
          <Plus size={20} />
          New Chat
        </button>
{/* History */}
<div className="mt-9 flex-1 min-h-0 overflow-y-auto">

  <p className="text-zinc-500 text-xs font-semibold mb-4 tracking-wider">
    YOUR HISTORY
  </p>

  {historyLoading ? (
    <p className="text-zinc-500 text-sm">
      Loading conversations...
    </p>
  ) : conversations.length > 0 ? (
    <div className="space-y-2">

      {conversations.map((conversation) => (
        <button
          key={conversation.id}
          onClick={() => handleSelectConversation(conversation.id)}
          className={`w-full flex items-center gap-3 text-sm text-left p-3 rounded-lg transition ${
            conversationId === conversation.id
              ? 'bg-zinc-800 text-white'
              : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
          }`}
        >
          <MessageSquare size={17} className="shrink-0" />

          <span className="truncate">
            {conversation.title || 'Untitled conversation'}
          </span>
        </button>
      ))}

    </div>
  ) : (
    <p className="text-zinc-500 text-sm">
      No conversations yet
    </p>
  )}

</div>

        {/* Sidebar Footer */}
        <div className="mt-auto border-t border-zinc-800 pt-4">
          <p className="text-xs text-zinc-500">
            YouTube AI Assistant
          </p>
          <p className="text-xs text-zinc-600 mt-1">
            Powered by AI
          </p>
        </div>

      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0 flex flex-col">

        {/* Top Navigation */}
        <header className="sticky top-0 z-30 bg-[#09090b]/90 backdrop-blur-md border-b border-zinc-800 px-4 sm:px-6 py-4 flex items-center gap-4">

          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden p-2 rounded-lg hover:bg-zinc-800 transition"
            aria-label="Open sidebar"
          >
            <Menu size={23} />
          </button>

          <div className="flex items-center gap-2">
            <Play size={21} className="text-red-500" />
            <span className="font-semibold">YouTube AI Assistant</span>
          </div>

        </header>

        {/* Main Workspace */}
        <div className="w-full max-w-6xl mx-auto px-4 py-6 sm:px-6 sm:py-8 md:px-10 md:py-10">

          <div className="mb-7 sm:mb-10">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold">
              Understand any YouTube video
            </h2>

            <p className="text-zinc-400 mt-2 text-sm sm:text-base">
              Paste a video link and start asking questions.
            </p>
          </div>

          <section className="w-full max-w-4xl mx-auto">

            {/* Video URL Input */}
            <form
              onSubmit={handleVideoSubmit}
              className="flex flex-col sm:flex-row gap-3 w-full"
            >
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Paste your YouTube video URL..."
                className="min-w-0 flex-1 w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 sm:py-4 outline-none focus:border-red-500 transition"
              />

              <button
                type="submit"
                disabled={processing}
                className="w-full sm:w-auto bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-3 sm:py-4 rounded-xl font-medium transition"
              >
                {processing ? 'Processing...' : 'Process'}
            </button>
            </form>
            {processing && (
              <p className="text-yellow-400 text-sm mt-3">
                Processing video and storing transcript...
              </p>
            )}

            {processed && (
              <p className="text-green-400 text-sm mt-3">
                Video processed successfully! You can now ask questions.
              </p>
            )}

            {videoError && (
              <p className="text-red-400 text-sm mt-3">
                {videoError}
              </p>
            )}

            {/* Video Player Placeholder */}
            {/* YouTube Video Player */}
            <div className="mt-6 sm:mt-8 w-full aspect-video bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">

              {videoUrl ? (
                <iframe
                  className="w-full h-full"
                  src={`https://www.youtube.com/embed/${extractVideoId(videoUrl)}`}
                  title="YouTube video player"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  referrerPolicy="strict-origin-when-cross-origin"
                  allowFullScreen
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <p className="text-zinc-500 text-sm text-center px-4">
                    Your YouTube video will appear here.
                  </p>
                </div>
              )}

            </div>
            {/* Chat Section */}
            <div className="mt-7 sm:mt-10">

              <h3 className="font-semibold text-base sm:text-lg mb-4">
                Ask about this video
              </h3>

              <div
                ref={chatContainerRef}
                className="w-full min-h-48 max-h-[450px] overflow-y-auto bg-zinc-900 border border-zinc-800 rounded-xl p-3 sm:p-5 space-y-4"
>

                {messages.length === 0 ? (
                  <p className="text-zinc-500 text-center text-sm mt-12">
                    Your conversation will appear here.
                  </p>
                ) : (
                  messages.map((message, index) => (
                    <div
                      key={index}
                      className={`p-3 sm:p-4 rounded-lg text-sm sm:text-base break-words ${
                        message.role === "user"
                          ? "bg-zinc-800 ml-auto"
                          : "bg-zinc-700 mr-auto"
                      }`}
                    >
                      <p className="text-xs text-zinc-400 mb-2">
                        {message.role === "user" ? "You" : "AI Assistant"}
                      </p>

                      {message.role === "assistant" ? (
                      <div className="
                        text-sm sm:text-base leading-7
                        [&_h1]:text-xl [&_h1]:font-bold [&_h1]:my-3
                        [&_h2]:text-lg [&_h2]:font-bold [&_h2]:my-3
                        [&_h3]:text-base [&_h3]:font-semibold [&_h3]:my-2
                        [&_p]:my-2
                        [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:my-2
                        [&_ol]:list-decimal [&_ol]:pl-6 [&_ol]:my-2
                        [&_li]:my-1
                        [&_strong]:font-bold
                        [&_a]:text-blue-400 [&_a]:underline
                        [&_blockquote]:border-l-4 [&_blockquote]:border-zinc-500
                        [&_blockquote]:pl-4 [&_blockquote]:italic
                        [&_pre]:bg-black [&_pre]:p-4 [&_pre]:rounded-lg
                        [&_pre]:overflow-x-auto [&_pre]:my-3
                        [&_code]:bg-black/50 [&_code]:px-1 [&_code]:rounded
                        [&_table]:w-full [&_table]:border-collapse
                        [&_th]:border [&_th]:border-zinc-600 [&_th]:p-2
                        [&_td]:border [&_td]:border-zinc-700 [&_td]:p-2
                      ">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                    </div>
                ))
                )}

              </div>
              {loading && (
              <p className="text-zinc-400 text-sm mt-3">
                AI is thinking...
              </p>
            )}

            {chatError && (
              <p className="text-red-500 text-sm mt-3">
                {chatError}
              </p>
            )}

              {/* Message Input */}
              <form
                onSubmit={handleSendMessage}
                className="flex flex-col sm:flex-row gap-3 mt-4"
              >
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about the video..."
                  className="min-w-0 flex-1 w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 sm:py-4 outline-none focus:border-red-500 transition"
                />

                <button
                  type="submit"
                  disabled={loading || !processed}
                  className="w-full sm:w-auto bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-3 sm:py-4 rounded-xl font-medium transition"
                >
                  {loading ? "Thinking..." : "Send"}
              </button>

              </form>

            </div>

          </section>
        </div>
      </main>
    </div>
  )
}

export default App
