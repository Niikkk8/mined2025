import React, { createContext, useContext, useState } from 'react';

const PodcastContext = createContext();

export const PodcastProvider = ({ children }) => {
    const [conversation, setConversation] = useState([]);
    const [paperDetails, setPaperDetails] = useState({ title: '', topic: '' });
    const [isGenerating, setIsGenerating] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(-1);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);

    return (
        <PodcastContext.Provider value={{
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
        }}>
            {children}
        </PodcastContext.Provider>
    );
};

export const usePodcast = () => useContext(PodcastContext);