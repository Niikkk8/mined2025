import React from 'react';
import { useAnimation } from '../context/AnimationContext';

export const AnimationControls = () => {
    const { maleAnimation, setMaleAnimation, femaleAnimation, setFemaleAnimation } = useAnimation();
    const animations = ["Idle", "Greeting", "Talking"];

    return (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 flex flex-col gap-4 bg-white/90 p-6 rounded-lg shadow-lg z-10">
            {/* Male Controls */}
            <div className="space-y-2">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Male Character</h3>
                <div className="flex gap-2">
                    {animations.map((anim) => (
                        <button
                            key={`male-${anim}`}
                            onClick={() => setMaleAnimation(anim)}
                            className={`px-4 py-2 rounded-md transition-colors ${maleAnimation === anim
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                                }`}
                        >
                            {anim}
                        </button>
                    ))}
                </div>
            </div>

            {/* Female Controls */}
            <div className="space-y-2">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Female Character</h3>
                <div className="flex gap-2">
                    {animations.map((anim) => (
                        <button
                            key={`female-${anim}`}
                            onClick={() => setFemaleAnimation(anim)}
                            className={`px-4 py-2 rounded-md transition-colors ${femaleAnimation === anim
                                    ? 'bg-pink-600 text-white'
                                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                                }`}
                        >
                            {anim}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};