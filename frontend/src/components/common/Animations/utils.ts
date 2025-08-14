/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * Animation Utilities - Helper Functions for Animation System
 */

import { Variants, Transition } from 'framer-motion';
import { 
  SlideDirection, 
  PageTransitionType, 
  AnimationConfig,
  ExtendedVariants 
} from './types';

// Check if user prefers reduced motion
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

// Get appropriate animation duration based on user preferences
export const getAnimationDuration = (baseDuration: number): number => {
  return prefersReducedMotion() ? baseDuration * 0.5 : baseDuration;
};

// Create slide variants based on direction
export const createSlideVariants = (direction: SlideDirection, distance = 50): Variants => {
  const getInitialPosition = () => {
    switch (direction) {
      case 'left':
        return { x: -distance, opacity: 0 };
      case 'right':
        return { x: distance, opacity: 0 };
      case 'up':
        return { y: -distance, opacity: 0 };
      case 'down':
        return { y: distance, opacity: 0 };
      default:
        return { x: -distance, opacity: 0 };
    }
  };

  const getExitPosition = () => {
    switch (direction) {
      case 'left':
        return { x: distance, opacity: 0 };
      case 'right':
        return { x: -distance, opacity: 0 };
      case 'up':
        return { y: distance, opacity: 0 };
      case 'down':
        return { y: -distance, opacity: 0 };
      default:
        return { x: distance, opacity: 0 };
    }
  };

  return {
    initial: getInitialPosition(),
    animate: { x: 0, y: 0, opacity: 1 },
    exit: getExitPosition(),
  };
};

// Create stagger variants with custom delay
export const createStaggerVariants = (
  baseVariants: Variants,
  staggerDelay = 0.1
): Variants => ({
  initial: baseVariants.initial,
  animate: {
    ...baseVariants.animate,
    transition: {
      ...((baseVariants.animate as any)?.transition || {}),
      staggerChildren: staggerDelay,
      delayChildren: staggerDelay,
    },
  },
  exit: {
    ...baseVariants.exit,
    transition: {
      ...((baseVariants.exit as any)?.transition || {}),
      staggerChildren: staggerDelay * 0.5,
      staggerDirection: -1,
    },
  },
});

// Get page transition variants by type
export const getPageTransitionVariants = (
  type: PageTransitionType,
  direction: SlideDirection = 'right'
): Variants => {
  switch (type) {
    case 'slide':
      return createSlideVariants(direction);
    case 'fade':
      return {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      };
    case 'scale':
      return {
        initial: { scale: 0.9, opacity: 0 },
        animate: { scale: 1, opacity: 1 },
        exit: { scale: 1.1, opacity: 0 },
      };
    case 'rotate':
      return {
        initial: { rotateY: 90, opacity: 0 },
        animate: { rotateY: 0, opacity: 1 },
        exit: { rotateY: -90, opacity: 0 },
      };
    case 'flip':
      return {
        initial: { rotateX: -90, opacity: 0 },
        animate: { rotateX: 0, opacity: 1 },
        exit: { rotateX: 90, opacity: 0 },
      };
    default:
      return createSlideVariants(direction);
  }
};

// Create responsive animation variants
export const createResponsiveVariants = (
  mobileVariants: Variants,
  desktopVariants: Variants
): Variants => {
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  return isMobile ? mobileVariants : desktopVariants;
};

// Animation timing functions
export const easings = {
  easeInQuad: [0.25, 0.46, 0.45, 0.94],
  easeOutQuad: [0.25, 0.46, 0.45, 0.94],
  easeInOutQuad: [0.455, 0.03, 0.515, 0.955],
  easeInCubic: [0.32, 0, 0.67, 0],
  easeOutCubic: [0.33, 1, 0.68, 1],
  easeInOutCubic: [0.65, 0, 0.35, 1],
  easeInExpo: [0.7, 0, 0.84, 0],
  easeOutExpo: [0.16, 1, 0.3, 1],
  easeInOutExpo: [0.87, 0, 0.13, 1],
  easeInBack: [0.36, 0, 0.66, -0.56],
  easeOutBack: [0.34, 1.56, 0.64, 1],
  easeInOutBack: [0.68, -0.6, 0.32, 1.6],
} as const;

// Create spring transition with presets
export const createSpringTransition = (
  preset: 'gentle' | 'wobbly' | 'stiff' | 'slow' | 'molasses' = 'gentle'
): Transition => {
  const presets = {
    gentle: { damping: 20, stiffness: 300 },
    wobbly: { damping: 10, stiffness: 200 },
    stiff: { damping: 30, stiffness: 400 },
    slow: { damping: 40, stiffness: 200 },
    molasses: { damping: 50, stiffness: 100 },
  };

  return {
    type: 'spring',
    ...presets[preset],
  };
};

// Create tween transition with easing
export const createTweenTransition = (
  duration = 0.3,
  easing: keyof typeof easings = 'easeInOutQuad',
  delay = 0
): Transition => ({
  duration,
  ease: easings[easing],
  delay,
});

// Combine multiple variants
export const combineVariants = (...variants: Variants[]): Variants => {
  return variants.reduce((combined, variant) => ({
    ...combined,
    ...variant,
  }), {});
};

// Create loading state variants
export const createLoadingVariants = (size = 24): Variants => ({
  idle: {
    opacity: 1,
    scale: 1,
  },
  loading: {
    opacity: 0.7,
    scale: 0.95,
    transition: {
      repeat: Infinity,
      repeatType: 'reverse',
      duration: 1,
    },
  },
  success: {
    opacity: 1,
    scale: 1.05,
    transition: {
      type: 'spring',
      damping: 15,
      stiffness: 300,
    },
  },
  error: {
    opacity: 1,
    scale: 1,
    x: [-2, 2, -2, 2, 0],
    transition: {
      duration: 0.4,
    },
  },
});

// Get safe animation config
export const getSafeAnimationConfig = (config: Partial<AnimationConfig>): AnimationConfig => ({
  pageTransitions: prefersReducedMotion() ? false : config.pageTransitions ?? true,
  microAnimations: prefersReducedMotion() ? false : config.microAnimations ?? true,
  reducedMotion: prefersReducedMotion(),
  staggerAnimations: prefersReducedMotion() ? false : config.staggerAnimations ?? true,
  scrollAnimations: prefersReducedMotion() ? false : config.scrollAnimations ?? true,
});

// Calculate stagger delay based on array length
export const calculateStaggerDelay = (
  arrayLength: number,
  maxDelay = 2,
  minDelay = 0.05
): number => {
  const delay = maxDelay / arrayLength;
  return Math.max(delay, minDelay);
};

// Create intersection observer for scroll animations
export const createIntersectionObserver = (
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: IntersectionObserverInit = {}
): IntersectionObserver => {
  const defaultOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px',
    ...options,
  };

  return new IntersectionObserver(callback, defaultOptions);
};

// Performance optimization utilities
export const shouldReduceMotion = (force?: boolean): boolean => {
  if (force !== undefined) return force;
  return prefersReducedMotion();
};

export const getOptimizedVariants = (
  variants: Variants,
  optimize = true
): Variants => {
  if (!optimize || shouldReduceMotion()) {
    // Return simplified variants for reduced motion
    return Object.keys(variants).reduce((simplified, key) => ({
      ...simplified,
      [key]: {
        opacity: key === 'initial' ? 0 : 1,
        transition: { duration: 0.01 },
      },
    }), {});
  }
  
  return variants;
};

// Generate random animation delay for organic feel
export const getRandomDelay = (min = 0, max = 0.5): number => {
  return Math.random() * (max - min) + min;
};

// Create hover scale effect
export const createHoverScale = (scale = 1.05, duration = 0.2): Variants => ({
  rest: { scale: 1 },
  hover: { 
    scale,
    transition: { duration }
  },
});

// Create ripple effect variants
export const createRippleVariants = (): Variants => ({
  initial: {
    scale: 0,
    opacity: 0.5,
  },
  animate: {
    scale: 1,
    opacity: 0,
    transition: {
      duration: 0.6,
      ease: 'easeOut',
    },
  },
});

// Utility to check if animations should be enabled
export const shouldAnimate = (config?: AnimationConfig): boolean => {
  if (shouldReduceMotion()) return false;
  if (!config) return true;
  return !config.reducedMotion;
};