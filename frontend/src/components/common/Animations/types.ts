/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * Animation Types - TypeScript Interfaces for Animation System
 */

import { Variants, Target, Transition } from 'framer-motion';
import { ReactNode } from 'react';

// Base animation props
export interface BaseAnimationProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

// Page transition types
export type PageTransitionType = 
  | 'slide'
  | 'fade'
  | 'scale'
  | 'rotate'
  | 'flip';

export type SlideDirection = 
  | 'left'
  | 'right'
  | 'up'
  | 'down';

// Animation component props
export interface AnimatedPageProps extends BaseAnimationProps {
  transition?: PageTransitionType;
  direction?: SlideDirection;
}

export interface AnimatedCardProps extends BaseAnimationProps {
  hoverEffect?: boolean;
  clickEffect?: boolean;
  elevation?: boolean;
  stagger?: boolean;
  index?: number;
}

export interface AnimatedListProps extends BaseAnimationProps {
  staggerDelay?: number;
  direction?: SlideDirection;
  threshold?: number;
}

export interface AnimatedButtonProps extends BaseAnimationProps {
  loading?: boolean;
  variant?: 'contained' | 'outlined' | 'text';
  size?: 'small' | 'medium' | 'large';
  pulseOnHover?: boolean;
}

export interface ScrollRevealProps extends BaseAnimationProps {
  threshold?: number;
  triggerOnce?: boolean;
  direction?: SlideDirection;
  distance?: number;
}

export interface StaggeredContainerProps extends BaseAnimationProps {
  staggerDelay?: number;
  reverse?: boolean;
}

export interface FloatingActionButtonProps extends BaseAnimationProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  icon?: ReactNode;
  onClick?: () => void;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  size?: 'small' | 'medium' | 'large';
}

export interface PageTransitionProps extends BaseAnimationProps {
  type?: PageTransitionType;
  direction?: SlideDirection;
  duration?: number;
}

// Animation configuration
export interface AnimationConfig {
  pageTransitions: boolean;
  microAnimations: boolean;
  reducedMotion: boolean;
  staggerAnimations: boolean;
  scrollAnimations: boolean;
}

// Motion variants type extensions
export interface ExtendedVariants extends Variants {
  [key: string]: Target | Variants;
}

// Animation context
export interface AnimationContextType {
  config: AnimationConfig;
  updateConfig: (config: Partial<AnimationConfig>) => void;
  prefersReducedMotion: boolean;
}

// Custom hook return types
export interface UseAnimationReturn {
  shouldAnimate: boolean;
  getVariants: (variantName: string) => Variants;
  getTransition: (transitionName: string) => Transition;
}

export interface UseScrollRevealReturn {
  ref: React.RefObject<Element>;
  isVisible: boolean;
  controls: any; // AnimationControls from framer-motion
}

export interface UseStaggerReturn {
  containerProps: {
    variants: Variants;
    initial: string;
    animate: string;
    exit: string;
  };
  itemProps: (index: number) => {
    variants: Variants;
    custom: number;
  };
}

// Loading states
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface LoadingAnimationProps {
  state: LoadingState;
  size?: number;
  color?: string;
}

// Gesture types
export type GestureType = 'hover' | 'tap' | 'drag' | 'focus' | 'pan';

export interface GestureConfig {
  [key: string]: boolean | number | string;
}

// Theme-aware animation
export interface ThemeAnimationProps {
  darkMode?: boolean;
  primaryColor?: string;
  accentColor?: string;
}

// Performance optimization types
export interface PerformanceConfig {
  willChange?: boolean;
  layoutId?: string;
  optimizeFor?: 'speed' | 'quality' | 'balanced';
}

// Animation event types
export interface AnimationEvents {
  onAnimationStart?: () => void;
  onAnimationComplete?: () => void;
  onAnimationUpdate?: (latest: any) => void;
}

// Combined animation props
export interface FullAnimationProps extends 
  BaseAnimationProps, 
  AnimationEvents, 
  PerformanceConfig, 
  ThemeAnimationProps {
  variants?: ExtendedVariants;
  transition?: Transition;
  gestures?: GestureConfig;
}