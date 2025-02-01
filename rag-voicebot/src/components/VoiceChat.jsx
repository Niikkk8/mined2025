import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, X, User, Bot } from 'lucide-react';

export const VoiceChat = ({ 
    onStartTalking, 
    onStopTalking, 
    onClose, 
    documentContext,
    apiUrl 
}) => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const recognitionRef = useRef(null);
    const [chatHistory, setChatHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const chatContainerRef = useRef(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [chatHistory]);

    const initializeSpeechRecognition = () => {
        if (typeof window === 'undefined') return;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error('Speech recognition not supported');
            return;
        }

        if (!recognitionRef.current) {
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = true;
            recognitionRef.current.interimResults = true;

            recognitionRef.current.onstart = () => {
                setIsListening(true);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current.onresult = (event) => {
                const current = event.resultIndex;
                const transcriptText = event.results[current][0].transcript;
                setTranscript(transcriptText);

                if (event.results[current].isFinal) {
                    handleUserInput(transcriptText);
                }
            };
        }
    };

    const handleUserInput = async (input) => {
        try {
            setIsLoading(true);
            onStartTalking();

            const userMessage = { type: "user", content: input };
            setChatHistory(prev => [...prev, userMessage]);

            const response = await fetch(`${apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: input,
                    context: documentContext.text + '\n\nSummary:\n' + documentContext.summary
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get response');
            }

            const data = await response.json();
            const botMessage = { type: "bot", content: data.response };
            setChatHistory(prev => [...prev, botMessage]);

            speakResponse(data.response);
        } catch (error) {
            console.error('Error:', error);
            onStopTalking();
            const errorMessage = "I encountered an error. Please try again.";
            speakResponse(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const speakResponse = (text) => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1;
        utterance.pitch = 1;
        utterance.volume = 1;

        utterance.onstart = () => {
            console.log('Speech started');
        };

        utterance.onend = () => {
            console.log('Speech ended');
            onStopTalking();
        };

        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event);
            onStopTalking();
        };

        window.speechSynthesis.speak(utterance);
    };

    const toggleListening = async () => {
        try {
            await initializeSpeechRecognition();

            if (!recognitionRef.current) return;

            if (isListening) {
                recognitionRef.current.stop();
            } else {
                recognitionRef.current.start();
            }
        } catch (error) {
            console.error('Error toggling listening state:', error);
        }
    };

    useEffect(() => {
        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            window.speechSynthesis.cancel();
        };
    }, []);

    return (
        <div className="flex flex-col h-[500px]">
            <div className="flex justify-between items-center p-4 border-b">
                <h2 className="text-lg font-semibold">Virtual Assistant</h2>
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-gray-100 rounded-full"
                >
                    <X size={20} />
                </button>
            </div>

            <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-4 space-y-4"
            >
                {documentContext.text && (
                    <div className="bg-blue-50 p-4 rounded-lg mb-4">
                        <p className="text-sm text-blue-800">
                            Document loaded. You can ask questions about its content.
                        </p>
                    </div>
                )}

                {chatHistory.map((msg, index) => (
                    <div
                        key={index}
                        className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div className={`flex items-start max-w-[80%] space-x-2 
                            ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                        >
                            <div className={`p-2 rounded-lg ${msg.type === 'user'
                                    ? 'bg-blue-500 text-white rounded-br-none'
                                    : 'bg-gray-100 text-black rounded-bl-none'
                                }`}>
                                {msg.content}
                            </div>
                            <div className={`p-1 rounded-full ${msg.type === 'user' ? 'bg-blue-100' : 'bg-gray-200'
                                }`}>
                                {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                            </div>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 p-3 rounded-lg">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="p-4 border-t bg-gray-50">
                {transcript && (
                    <div className="mb-2 text-sm text-gray-600">
                        {transcript}
                    </div>
                )}
                <div className="flex items-center justify-center">
                    <button
                        onClick={toggleListening}
                        disabled={isLoading}
                        className={`p-4 rounded-full transition-all duration-300 ${isListening
                                ? 'bg-red-500 hover:bg-red-600'
                                : 'bg-blue-500 hover:bg-blue-600'
                            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isListening ? (
                            <MicOff className="text-white" size={24} />
                        ) : (
                            <Mic className="text-white" size={24} />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};