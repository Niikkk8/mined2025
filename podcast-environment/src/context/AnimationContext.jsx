import React, { createContext, useContext, useState } from 'react';

export const AnimationContext = createContext();

export const AnimationProvider = ({ children }) => {
    const [maleAnimation, setMaleAnimation] = useState("Idle");
    const [femaleAnimation, setFemaleAnimation] = useState("Idle");

    return (
        <AnimationContext.Provider value={{
            maleAnimation,
            setMaleAnimation,
            femaleAnimation,
            setFemaleAnimation
        }}>
            {children}
        </AnimationContext.Provider>
    );
};

export const useAnimation = () => useContext(AnimationContext);
