import React, { useEffect, useRef } from 'react';
import { usePodcast } from '../context/PodcastContext';

export const ChatHistory = () => {
    const { conversation, currentIndex } = usePodcast();
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [currentIndex]);

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

    return (
        <div className="fixed right-4 top-24 w-80 bg-black/20 backdrop-blur-sm rounded-lg p-4 text-white h-[calc(100vh-120px)]">
            <div className="h-full flex flex-col">
                <div className="overflow-y-auto flex-1 pr-2 space-y-4" ref={scrollRef}>
                    {conversation.slice(0, currentIndex + 1).map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex flex-col ${msg.speaker === 'Host' ? 'items-end' : 'items-start'}`}
                        >
                            <div className={`max-w-[90%] p-3 rounded-lg ${msg.speaker === 'Host'
                                    ? 'bg-blue-500 rounded-tr-none'
                                    : 'bg-pink-500 rounded-tl-none'
                                }`}>
                                <div className="text-xs opacity-75 mb-1">
                                    {msg.speaker}
                                </div>
                                <div>
                                    {cleanMessage(msg.message)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};