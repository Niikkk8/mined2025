import React, { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useGraph } from '@react-three/fiber'
import { useAnimations, useFBX, useGLTF } from '@react-three/drei'
import { SkeletonUtils } from 'three-stdlib'

export function Avatar({ animation = "Idle", ...props }) {
  const { scene } = useGLTF('/models/6798708d7e1d9806c1e265b3.glb')
  const clone = React.useMemo(() => SkeletonUtils.clone(scene), [scene])
  const { nodes, materials } = useGraph(clone)

  const { animations: idleAnimation } = useFBX("/animations/Breathing Idle.fbx")
  const { animations: talkingAnimation } = useFBX("/animations/Talking.fbx")

  const remapBoneNames = (animClip) => {
    const newTracks = animClip.tracks.map(track => {
      const newTrack = track.clone();
      newTrack.name = track.name.replace('mixamorig', '');
      return newTrack;
    });

    return new THREE.AnimationClip(
      animClip.name,
      animClip.duration,
      newTracks,
      animClip.blendMode
    );
  }

  idleAnimation[0].name = "Idle"
  talkingAnimation[0].name = "Talking"

  const mappedIdleAnimation = remapBoneNames(idleAnimation[0])
  const mappedTalkingAnimation = remapBoneNames(talkingAnimation[0])

  const group = useRef()
  const { actions } = useAnimations([mappedIdleAnimation, mappedTalkingAnimation], group)

  useEffect(() => {
    Object.values(actions).forEach((action) => {
      if (action.isRunning()) {
        action.fadeOut(0.2);
      }
    });

    if (actions[animation]) {
      actions[animation].reset().fadeIn(0.2).play();
    }
  }, [animation, actions]);

  return (
    <group {...props} dispose={null} ref={group}>
      <primitive object={nodes.Hips} />
      <skinnedMesh geometry={nodes.Wolf3D_Hair.geometry} material={materials.Wolf3D_Hair} skeleton={nodes.Wolf3D_Hair.skeleton} />
      <skinnedMesh geometry={nodes.Wolf3D_Body.geometry} material={materials.Wolf3D_Body} skeleton={nodes.Wolf3D_Body.skeleton} />
      <skinnedMesh geometry={nodes.Wolf3D_Outfit_Bottom.geometry} material={materials.Wolf3D_Outfit_Bottom} skeleton={nodes.Wolf3D_Outfit_Bottom.skeleton} />
      <skinnedMesh geometry={nodes.Wolf3D_Outfit_Footwear.geometry} material={materials.Wolf3D_Outfit_Footwear} skeleton={nodes.Wolf3D_Outfit_Footwear.skeleton} />
      <skinnedMesh geometry={nodes.Wolf3D_Outfit_Top.geometry} material={materials.Wolf3D_Outfit_Top} skeleton={nodes.Wolf3D_Outfit_Top.skeleton} />
      <skinnedMesh name="EyeLeft" geometry={nodes.EyeLeft.geometry} material={materials.Wolf3D_Eye} skeleton={nodes.EyeLeft.skeleton} morphTargetDictionary={nodes.EyeLeft.morphTargetDictionary} morphTargetInfluences={nodes.EyeLeft.morphTargetInfluences} />
      <skinnedMesh name="EyeRight" geometry={nodes.EyeRight.geometry} material={materials.Wolf3D_Eye} skeleton={nodes.EyeRight.skeleton} morphTargetDictionary={nodes.EyeRight.morphTargetDictionary} morphTargetInfluences={nodes.EyeRight.morphTargetInfluences} />
      <skinnedMesh name="Wolf3D_Head" geometry={nodes.Wolf3D_Head.geometry} material={materials.Wolf3D_Skin} skeleton={nodes.Wolf3D_Head.skeleton} morphTargetDictionary={nodes.Wolf3D_Head.morphTargetDictionary} morphTargetInfluences={nodes.Wolf3D_Head.morphTargetInfluences} />
      <skinnedMesh name="Wolf3D_Teeth" geometry={nodes.Wolf3D_Teeth.geometry} material={materials.Wolf3D_Teeth} skeleton={nodes.Wolf3D_Teeth.skeleton} morphTargetDictionary={nodes.Wolf3D_Teeth.morphTargetDictionary} morphTargetInfluences={nodes.Wolf3D_Teeth.morphTargetInfluences} />
    </group>
  )
}

useGLTF.preload('/models/6798708d7e1d9806c1e265b3.glb')