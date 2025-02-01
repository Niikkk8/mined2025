import React, { useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { usePodcast } from '../context/PodcastContext';
import { fetchBackgroundImages } from '../services/imageService';
import * as THREE from 'three';
import { useTexture } from '@react-three/drei';

const DynamicBackground = () => {
    const { viewport } = useThree();
    const { paperDetails } = usePodcast();
    const materialRef = useRef();
    const texturesRef = useRef({
        current: null,
        next: null,
        images: [],
        currentIndex: 0,
        transitionProgress: 0
    });

    // Load static background
    const staticBackground = useTexture('/textures/static-initial-background.png');
    
    // Ensure proper texture settings
    useEffect(() => {
        if (staticBackground) {
            staticBackground.wrapS = staticBackground.wrapT = THREE.ClampToEdgeWrapping;
            staticBackground.minFilter = THREE.LinearFilter;
            staticBackground.magFilter = THREE.LinearFilter;
            staticBackground.needsUpdate = true;
        }
    }, [staticBackground]);

    // Setup shader material with initial static background
    useEffect(() => {
        materialRef.current = new THREE.ShaderMaterial({
            uniforms: {
                currentTexture: { value: staticBackground },
                nextTexture: { value: staticBackground },
                transition: { value: 0 }
            },
            vertexShader: `
                varying vec2 vUv;
                void main() {
                    vUv = uv;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform sampler2D currentTexture;
                uniform sampler2D nextTexture;
                uniform float transition;
                varying vec2 vUv;

                void main() {
                    vec4 current = texture2D(currentTexture, vUv);
                    vec4 next = texture2D(nextTexture, vUv);
                    gl_FragColor = mix(current, next, transition);
                }
            `
        });
    }, [staticBackground]);

    // Fetch images when paper details change
    useEffect(() => {
        if (paperDetails.topic) {
            const loadImages = async () => {
                const images = await fetchBackgroundImages(paperDetails.topic);
                if (images.length > 0) {
                    const loader = new THREE.TextureLoader();
                    const loadedTextures = await Promise.all(
                        images.map(url => 
                            new Promise((resolve) => {
                                loader.load(url, (texture) => {
                                    texture.wrapS = texture.wrapT = THREE.ClampToEdgeWrapping;
                                    texture.minFilter = THREE.LinearFilter;
                                    texture.magFilter = THREE.LinearFilter;
                                    texture.needsUpdate = true;
                                    resolve(texture);
                                });
                            })
                        )
                    );
                    
                    texturesRef.current.images = loadedTextures;
                    texturesRef.current.current = loadedTextures[0];
                    texturesRef.current.next = loadedTextures[1] || loadedTextures[0];
                    
                    if (materialRef.current) {
                        materialRef.current.uniforms.currentTexture.value = texturesRef.current.current;
                        materialRef.current.uniforms.nextTexture.value = texturesRef.current.next;
                    }
                }
            };

            loadImages();
        }
    }, [paperDetails.topic]);

    // Handle animation
    useFrame((_, delta) => {
        if (!materialRef.current || texturesRef.current.images.length < 2) return;

        texturesRef.current.transitionProgress += delta * 0.2;

        if (texturesRef.current.transitionProgress >= 1) {
            texturesRef.current.transitionProgress = 0;
            texturesRef.current.currentIndex = 
                (texturesRef.current.currentIndex + 1) % texturesRef.current.images.length;
            
            texturesRef.current.current = texturesRef.current.images[texturesRef.current.currentIndex];
            texturesRef.current.next = texturesRef.current.images[
                (texturesRef.current.currentIndex + 1) % texturesRef.current.images.length
            ];

            materialRef.current.uniforms.currentTexture.value = texturesRef.current.current;
            materialRef.current.uniforms.nextTexture.value = texturesRef.current.next;
        }

        materialRef.current.uniforms.transition.value = texturesRef.current.transitionProgress;
    });

    return (
        <mesh position={[0, 0, 1]}>
            <planeGeometry args={[viewport.width, viewport.height]} />
            {materialRef.current && <primitive object={materialRef.current} attach="material" />}
        </mesh>
    );
};

export default DynamicBackground;