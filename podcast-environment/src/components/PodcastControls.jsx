import React, { useEffect, useRef, useState } from 'react';
import { usePodcast } from '../context/PodcastContext';
import { useAnimation } from '../context/AnimationContext';
import { ChatHistory } from './ChatHistory';

const INTRO_MESSAGE = "Welcome to our Research Podcast! Today we'll be discussing an exciting paper.";

export const PodcastControls = () => {
    const {
        conversation,
        setConversation,
        paperDetails,
        setPaperDetails,
        isGenerating,
        setIsGenerating,
        currentIndex,
        setCurrentIndex,
        isPlaying,
        setIsPlaying,
        isSpeaking,
        setIsSpeaking
    } = usePodcast();

    const { setMaleAnimation, setFemaleAnimation } = useAnimation();
    const speakingRef = useRef(null);
    const voicesLoadedRef = useRef(false);
    const [availableVoices, setAvailableVoices] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    
    // Updated preferences state with proper initial values
    const [preferences, setPreferences] = useState({
        length: 'medium',
        tone: 'casual',
        detailLevel: 'overview',
        targetAudience: 'general',
        speakingPace: 'normal',
        includedSections: {
            methodology: true,
            results: true,
            implications: true,
            limitations: true,
            futureWork: true
        }
    });

    // Form options with proper value/label pairs
    const formOptions = [
        { 
            label: 'Podcast Length', 
            name: 'length', 
            options: [
                { value: 'short', label: 'Short (5-10 minutes)' },
                { value: 'medium', label: 'Medium (10-15 minutes)' },
                { value: 'long', label: 'Long (15-20 minutes)' }
            ]
        },
        { 
            label: 'Conversation Tone', 
            name: 'tone', 
            options: [
                { value: 'casual', label: 'Casual & Conversational' },
                { value: 'professional', label: 'Professional' },
                { value: 'academic', label: 'Academic' }
            ]
        },
        { 
            label: 'Detail Level', 
            name: 'detailLevel', 
            options: [
                { value: 'overview', label: 'High-level Overview' },
                { value: 'balanced', label: 'Balanced' },
                { value: 'detailed', label: 'In-depth Details' }
            ]
        },
        { 
            label: 'Target Audience', 
            name: 'targetAudience', 
            options: [
                { value: 'general', label: 'General Public' },
                { value: 'academic', label: 'Academic Researchers' },
                { value: 'industry', label: 'Industry Professionals' }
            ]
        },
        { 
            label: 'Speaking Pace', 
            name: 'speakingPace', 
            options: [
                { value: 'slow', label: 'Slow & Clear' },
                { value: 'normal', label: 'Normal' },
                { value: 'fast', label: 'Fast-paced' }
            ]
        }
    ];

    const cleanMessage = (message) => {
        return message
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\[(.*?)\]/g, '')
            .replace(/\(\d{2}:\d{2}:\d{2}\)/g, '')
            .replace(/\(.*?\)/g, '')
            .replace(/^(Host|Guest):\s*/i, '')
            .replace(/^(Host|Guest)\s*/i, '')
            .trim();
    };

    const selectVoice = (isMale) => {
        if (!availableVoices.length) return null;

        const preferredVoices = isMale
            ? ['Google UK English Male', 'Microsoft David', 'Male']
            : ['Google UK English Female', 'Microsoft Zira', 'Female'];

        for (const preferred of preferredVoices) {
            const voice = availableVoices.find(v =>
                v.name.includes(preferred) ||
                v.name.toLowerCase().includes(preferred.toLowerCase())
            );
            if (voice) return voice;
        }

        return availableVoices[0];
    };

    const speakText = async (text, isMale = true) => {
        return new Promise((resolve) => {
            if (speakingRef.current) {
                speechSynthesis.cancel();
            }

            const utterance = new SpeechSynthesisUtterance(text);
            const selectedVoice = selectVoice(isMale);

            if (selectedVoice) {
                utterance.voice = selectedVoice;
            }

            utterance.rate = preferences.speakingPace === 'slow' ? 0.8 : 
                           preferences.speakingPace === 'fast' ? 1.2 : 1;
            utterance.pitch = isMale ? 0.9 : 1.1;
            utterance.volume = 1.0;

            utterance.onend = () => {
                setIsSpeaking(false);
                resolve();
            };

            utterance.onerror = (event) => {
                console.error('Speech synthesis error:', event);
                setIsSpeaking(false);
                resolve();
            };

            speakingRef.current = utterance;
            setIsSpeaking(true);

            const sentences = text.split(/[.!?]+/).filter(Boolean);
            sentences.forEach((sentence, index) => {
                setTimeout(() => {
                    const utterance = new SpeechSynthesisUtterance(sentence + '.');
                    utterance.voice = selectedVoice;
                    utterance.rate = preferences.speakingPace === 'slow' ? 0.8 : 
                                   preferences.speakingPace === 'fast' ? 1.2 : 1;
                    utterance.pitch = isMale ? 0.9 : 1.1;
                    utterance.volume = 1.0;

                    if (index === sentences.length - 1) {
                        utterance.onend = () => {
                            setIsSpeaking(false);
                            resolve();
                        };
                    }

                    speechSynthesis.speak(utterance);
                }, index * 100);
            });
        });
    };

    const prepareNextLine = async () => {
        if (!isPlaying || isSpeaking) return;

        const nextIndex = currentIndex + 1;

        if (currentIndex === -1) {
            setMaleAnimation('Greeting');
            setFemaleAnimation('Greeting');
            await speakText(INTRO_MESSAGE);
            await new Promise(resolve => setTimeout(resolve, 500));
            setCurrentIndex(nextIndex);
            const firstMessage = cleanMessage(conversation[0].message);
            await speakText(firstMessage, true);
            setMaleAnimation('Idle');
            return;
        }

        setCurrentIndex(nextIndex);

        if (nextIndex >= conversation.length) {
            setIsPlaying(false);
            setMaleAnimation('Idle');
            setFemaleAnimation('Idle');
            return;
        }

        const message = cleanMessage(conversation[nextIndex].message);
        const isHost = conversation[nextIndex].speaker === 'Host';

        try {
            if (isHost) {
                setMaleAnimation('Talking');
                setFemaleAnimation('Idle');
                await speakText(message, true);
                setMaleAnimation('Idle');
            } else {
                setMaleAnimation('Idle');
                setFemaleAnimation('Talking');
                await speakText(message, false);
                setFemaleAnimation('Idle');
            }
        } catch (error) {
            console.error('Speech error:', error);
            setIsSpeaking(false);
        }
    };

    const handlePreferenceChange = (e) => {
        const { name, value, type, checked } = e.target;
        setPreferences(prev => {
            if (type === 'checkbox') {
                return {
                    ...prev,
                    includedSections: {
                        ...prev.includedSections,
                        [name]: checked
                    }
                };
            }
            return {
                ...prev,
                [name]: value
            };
        });
    };

    const handleFileSelect = (event) => {
        const file = event.target.files[0];
        if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please upload a PDF file');
            return;
        }
        setSelectedFile(file);
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        setIsGenerating(true);
        setShowModal(false);

        const formData = new FormData();
        formData.append('pdf', selectedFile);
        formData.append('preferences', JSON.stringify(preferences));

        try {
            const response = await fetch('http://localhost:5000/api/generate-podcast', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to generate podcast');
            }

            const data = await response.json();

            if (!data.conversation || !Array.isArray(data.conversation)) {
                throw new Error('Invalid response format from server');
            }

            setConversation(data.conversation);
            setPaperDetails({
                title: data.title || 'Untitled Paper',
                topic: data.topic || 'General Research',
                keywords: data.keywords || []
            });
            setCurrentIndex(-1);
            setIsPlaying(false);
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Error generating podcast. Please try again.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handlePlayPause = () => {
        if (conversation.length === 0) return;

        if (currentIndex + 1 >= conversation.length) {
            setCurrentIndex(-1);
        }

        if (isSpeaking) {
            speechSynthesis.cancel();
            setIsSpeaking(false);
        }

        setIsPlaying(!isPlaying);
    };

    const handleReset = () => {
        if (isSpeaking) {
            speechSynthesis.cancel();
            setIsSpeaking(false);
        }
        setCurrentIndex(-1);
        setIsPlaying(false);
        setMaleAnimation('Idle');
        setFemaleAnimation('Idle');
        setSelectedFile(null);
        setShowModal(false);
    };

    useEffect(() => {
        const loadVoices = () => {
            const voices = speechSynthesis.getVoices();
            if (voices.length > 0) {
                setAvailableVoices(voices);
                voicesLoadedRef.current = true;
            }
        };

        loadVoices();
        speechSynthesis.onvoiceschanged = loadVoices;

        return () => {
            if (speakingRef.current) {
                speechSynthesis.cancel();
            }
        };
    }, []);

    useEffect(() => {
        if (isPlaying && !isSpeaking && voicesLoadedRef.current) {
            prepareNextLine();
        }
    }, [isPlaying, isSpeaking, currentIndex]);

    return (
        <div className="relative min-h-screen bg-gray-100 flex flex-col items-center px-4">
            {/* Main Controls */}
            <div className="fixed top-6 left-1/2 transform -translate-x-1/2 flex flex-col gap-4 
                          bg-black/30 backdrop-blur-md p-5 rounded-xl shadow-lg z-10">
                <div className="flex items-center gap-4">
                    {!conversation.length && (
                        <input
                            type="file"
                            accept=".pdf"
                            onChange={handleFileSelect}
                            className="file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 
                                     file:bg-gradient-to-r from-blue-500 to-indigo-500 file:text-white 
                                     hover:file:opacity-90 transition cursor-pointer"
                        />
                    )}
    
                    {conversation.length > 0 && (
                        <div className="flex gap-3">
                            <button
                                onClick={handlePlayPause}
                                className="px-5 py-2 rounded-lg bg-blue-600 text-white font-semibold 
                                         shadow-md hover:bg-blue-700 transition disabled:opacity-50"
                                disabled={isGenerating}
                            >
                                {isPlaying ? 'Pause' : 'Play'}
                            </button>
                            <button
                                onClick={handleReset}
                                className="px-5 py-2 rounded-lg bg-gray-600 text-white font-semibold 
                                         shadow-md hover:bg-gray-700 transition disabled:opacity-50"
                                disabled={isGenerating}
                            >
                                Reset
                            </button>
                        </div>
                    )}
                </div>
    
                {isGenerating && (
                    <div className="text-white animate-pulse text-center font-semibold">
                        Generating podcast script...
                    </div>
                )}
    
                {paperDetails.title && (
                    <div className="text-white text-center">
                        <h3 className="font-bold text-lg">{paperDetails.title}</h3>
                        <p className="text-sm opacity-80">{paperDetails.topic}</p>
                    </div>
                )}
            </div>
    
            {/* Preferences Modal */}
            {showModal && (
                <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
                    <div className="bg-white rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-lg mx-4">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-gray-900">Customize Your Podcast</h2>
                            <button 
                                onClick={() => setShowModal(false)}
                                className="text-gray-500 hover:text-gray-700 p-2 rounded-full transition"
                            >
                                ✕
                            </button>
                        </div>
    
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div className="space-y-4">
                                {formOptions.map(({ label, name, options }) => (
                                    <div key={name}>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            {label}
                                        </label>
                                        <select
                                            name={name}
                                            value={preferences[name]}
                                            onChange={handlePreferenceChange}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 
                                                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                                        >
                                            {options.map((option) => (
                                                <option key={option.value} value={option.value}>
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                ))}
                            </div>
    
                            {/* Checkbox Sections */}
                            <div className="mt-4">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Include Sections
                                </label>
                                <div className="grid grid-cols-2 gap-3">
                                    {Object.entries({
                                        methodology: 'Research Methodology',
                                        results: 'Key Results',
                                        implications: 'Practical Implications',
                                        limitations: 'Study Limitations',
                                        futureWork: 'Future Work'
                                    }).map(([key, label]) => (
                                        <label key={key} className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                name={key}
                                                checked={preferences.includedSections[key]}
                                                onChange={handlePreferenceChange}
                                                className="rounded border-gray-300 text-blue-500 
                                                         focus:ring-blue-500 transition"
                                            />
                                            <span className="text-sm text-gray-700">{label}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
    
                            {/* Modal Actions */}
                            <div className="flex gap-4 pt-5 border-t border-gray-200 mt-4">
                                <button
                                    type="submit"
                                    className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-500 text-white 
                                             font-semibold py-2 px-4 rounded-lg shadow-md hover:opacity-90 transition"
                                >
                                    Generate Podcast
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="flex-1 bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg 
                                             shadow-md hover:bg-gray-700 transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
    
            {/* Chat history component */}
            {conversation.length > 0 && <ChatHistory />}
        </div>
    );
};