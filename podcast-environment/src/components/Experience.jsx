import { useEffect } from "react";
import { useThree } from "@react-three/fiber";
import { AvatarMan } from "./AvatarMan";
import { AvatarWoman } from "./AvatarWoman";
import DynamicBackground from "./DynamicBackground";

export const Experience = () => {
  const { camera } = useThree();

  useEffect(() => {
    camera.position.set(0, 2, 8);
    camera.lookAt(0, 0, 0);
  }, [camera]);

  return (
    <>
      <DynamicBackground />

      {/* Characters */}
      <AvatarWoman position={[-1.5, -1.8, 4]} scale={2} />
      <AvatarMan position={[1.5, -1.8, 4]} scale={2} />

      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1.5} castShadow />
    </>
  );
};