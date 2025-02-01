import { Canvas } from "@react-three/fiber";
import { Experience } from "./components/Experience";
import { VoiceChat } from "./components/VoiceChat";
import { useState } from "react";
import { MessageCircle, X, Upload } from "lucide-react";

// API base URL - adjust this based on your Flask server
const API_URL = 'http://localhost:5000';

function App() {
  const [avatarAnimation, setAvatarAnimation] = useState("Idle");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [documentContext, setDocumentContext] = useState({
    text: "",
    summary: ""
  });

  const handleStartTalking = () => {
    setAvatarAnimation("Talking");
  };

  const handleStopTalking = () => {
    setAvatarAnimation("Idle");
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/api/process-file`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process file');
      }

      const data = await response.json();
      setDocumentContext({
        text: data.text,
        summary: data.summary
      });
      setIsChatOpen(true);
    } catch (err) {
      setError(err.message || 'Error processing file');
      console.error('Error details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <Canvas shadows camera={{ position: [0, 0, 8], fov: 42 }}>
        <color attach="background" args={["#ececec"]} />
        <Experience avatarAnimation={avatarAnimation} />
      </Canvas>

      {/* File Upload */}
      <div className="fixed top-8 left-8 z-20">
        <label className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-lg cursor-pointer hover:bg-gray-50">
          <Upload size={20} />
          <span>{isLoading ? 'Processing...' : 'Upload PDF'}</span>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
            disabled={isLoading}
          />
        </label>
      </div>

      {/* Error Display */}
      {error && (
        <div className="fixed top-20 left-8 p-4 bg-red-50 text-red-700 rounded-lg max-w-md z-20">
          {error}
        </div>
      )}

      {/* Chat toggle button */}
      <button
        onClick={toggleChat}
        className="fixed bottom-8 right-8 p-4 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all duration-300 z-20"
      >
        {isChatOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* Chat interface */}
      {isChatOpen && (
        <div className="fixed right-8 bottom-28 w-96 bg-white rounded-lg shadow-xl z-20">
          <VoiceChat
            onStartTalking={handleStartTalking}
            onStopTalking={handleStopTalking}
            onClose={toggleChat}
            documentContext={documentContext}
            apiUrl={API_URL}
          />
        </div>
      )}
    </div>
  );
}

export default App;