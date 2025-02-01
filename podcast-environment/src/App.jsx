import { PodcastProvider } from "./context/PodcastContext";
import { PodcastControls } from "./components/PodcastControls";
import { AnimationProvider } from "./context/AnimationContext";
import { Canvas } from "@react-three/fiber";
import { Experience } from "./components/Experience";
// import { AnimationControls } from "./components/AnimationControls";

function App() {
  return (
    <AnimationProvider>
      <PodcastProvider>
        <div style={styles.container}>
          <Canvas shadows camera={{ position: [0, 0, 8], fov: 42 }}>
            <color attach="background" args={["#f3f3f3"]} />
            <Experience />
          </Canvas>
          {/* <AnimationControls /> */}
          <div style={{ maxWidth: "90vw", overflowX: "auto" }}>
            <PodcastControls />
          </div>
        </div>
      </PodcastProvider>
    </AnimationProvider>
  );
}

const styles = {
  container: {
    width: "100vw",
    height: "100vh",
    overflow: "hidden",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "linear-gradient(to bottom, #dfe9f3, #ffffff)",
  },
};


export default App;
