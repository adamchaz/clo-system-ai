/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * Animation Hooks - Custom React hooks for animation management
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useAnimation, useInView } from 'framer-motion';
import { useLocalStorage } from 'react-use';
import {
  AnimationConfig,
  UseAnimationReturn,
  UseScrollRevealReturn,
  UseStaggerReturn,
  ExtendedVariants,
} from './types';
import {
  prefersReducedMotion,
  getSafeAnimationConfig,
  shouldAnimate,
  createStaggerVariants,
  getOptimizedVariants,
} from './utils';
import { Variants, Transition } from 'framer-motion';

// Main animation configuration hook
export const useAnimationConfig = (): {
  config: AnimationConfig;
  updateConfig: (newConfig: Partial<AnimationConfig>) => void;
  resetConfig: () => void;
} => {
  const [storedConfig, setStoredConfig] = useLocalStorage<Partial<AnimationConfig>>(
    'clo-animation-config',
    {}
  );

  const config = useMemo(() => 
    getSafeAnimationConfig(storedConfig || {}), 
    [storedConfig]
  );

  const updateConfig = useCallback((newConfig: Partial<AnimationConfig>) => {
    setStoredConfig(prev => ({ ...prev, ...newConfig }));
  }, [setStoredConfig]);

  const resetConfig = useCallback(() => {
    setStoredConfig({});
  }, [setStoredConfig]);

  return { config, updateConfig, resetConfig };
};

// Enhanced animation hook with configuration awareness
export const useEnhancedAnimation = (): UseAnimationReturn => {
  const { config } = useAnimationConfig();
  
  const shouldAnimateValue = useMemo(() => 
    shouldAnimate(config), 
    [config]
  );

  const getVariants = useCallback((variantName: string): Variants => {
    // This would typically import from a variants registry
    // For now, return basic variants
    return getOptimizedVariants({
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 },
    }, shouldAnimateValue);
  }, [shouldAnimateValue]);

  const getTransition = useCallback((transitionName: string): Transition => {
    if (!shouldAnimateValue) {
      return { duration: 0.01 };
    }

    const transitions = {
      smooth: { type: 'spring', damping: 25, stiffness: 120 },
      quick: { duration: 0.2, ease: 'easeOut' },
      slow: { duration: 0.5, ease: 'easeInOut' },
      bouncy: { type: 'spring', damping: 12, stiffness: 200 },
    };

    return transitions[transitionName as keyof typeof transitions] || transitions.smooth;
  }, [shouldAnimateValue]);

  return {
    shouldAnimate: shouldAnimateValue,
    getVariants,
    getTransition,
  };
};

// Scroll reveal hook with intersection observer
export const useScrollReveal = (
  threshold = 0.1,
  triggerOnce = true
): UseScrollRevealReturn => {
  const controls = useAnimation();
  const ref = useRef<Element>(null);
  const inView = useInView(ref as React.RefObject<Element>, { amount: threshold, once: triggerOnce });
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (inView) {
      setIsVisible(true);
      controls.start('visible');
    } else if (!triggerOnce) {
      setIsVisible(false);
      controls.start('hidden');
    }
  }, [inView, controls, triggerOnce]);

  return { ref: ref as React.RefObject<Element>, isVisible, controls };
};

// Stagger animation hook
export const useStagger = (
  baseVariants: Variants,
  staggerDelay = 0.1
): UseStaggerReturn => {
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();
  
  const containerVariants = useMemo(() => 
    createStaggerVariants(baseVariants, shouldAnimateValue ? staggerDelay : 0),
    [baseVariants, staggerDelay, shouldAnimateValue]
  );

  const containerProps = useMemo(() => ({
    variants: containerVariants,
    initial: 'initial',
    animate: 'animate',
    exit: 'exit',
  }), [containerVariants]);

  const itemProps = useCallback((index: number) => ({
    variants: baseVariants,
    custom: index,
  }), [baseVariants]);

  return { containerProps, itemProps };
};

// Reduced motion preference hook
export const useReducedMotion = (): {
  prefersReduced: boolean;
  forceReduced: boolean;
  setForceReduced: (force: boolean) => void;
} => {
  const [forceReduced, setForceReduced] = useState(false);
  const [prefersReduced, setPrefersReduced] = useState(prefersReducedMotion());

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReduced(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return {
    prefersReduced: prefersReduced || forceReduced,
    forceReduced,
    setForceReduced,
  };
};

// Page transition hook
export const usePageTransition = (
  transitionType: 'slide' | 'fade' | 'scale' = 'slide'
) => {
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();
  const controls = useAnimation();

  const startTransition = useCallback(async () => {
    if (!shouldAnimateValue) return;
    
    await controls.start('exit');
  }, [controls, shouldAnimateValue]);

  const completeTransition = useCallback(() => {
    if (!shouldAnimateValue) return;
    
    controls.start('animate');
  }, [controls, shouldAnimateValue]);

  const variants = useMemo(() => {
    if (!shouldAnimateValue) {
      return {
        initial: { opacity: 1 },
        animate: { opacity: 1 },
        exit: { opacity: 1 },
      };
    }

    switch (transitionType) {
      case 'slide':
        return {
          initial: { x: -20, opacity: 0 },
          animate: { x: 0, opacity: 1 },
          exit: { x: 20, opacity: 0 },
        };
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
      default:
        return {
          initial: { x: -20, opacity: 0 },
          animate: { x: 0, opacity: 1 },
          exit: { x: 20, opacity: 0 },
        };
    }
  }, [transitionType, shouldAnimateValue]);

  return {
    variants,
    controls,
    startTransition,
    completeTransition,
  };
};

// Hover animation hook
export const useHoverAnimation = (
  hoverVariants: Variants = {
    rest: { scale: 1 },
    hover: { scale: 1.05 },
  }
) => {
  const [isHovered, setIsHovered] = useState(false);
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();

  const hoverProps = useMemo(() => {
    if (!shouldAnimateValue) return {};

    return {
      variants: hoverVariants,
      initial: 'rest',
      animate: isHovered ? 'hover' : 'rest',
      onMouseEnter: () => setIsHovered(true),
      onMouseLeave: () => setIsHovered(false),
    };
  }, [hoverVariants, isHovered, shouldAnimateValue]);

  return { isHovered, hoverProps };
};

// Loading animation hook
export const useLoadingAnimation = (loading: boolean) => {
  const controls = useAnimation();
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();

  useEffect(() => {
    if (!shouldAnimateValue) return;

    if (loading) {
      controls.start('loading');
    } else {
      controls.start('idle');
    }
  }, [loading, controls, shouldAnimateValue]);

  const variants = useMemo(() => ({
    idle: {
      opacity: 1,
      scale: 1,
    },
    loading: {
      opacity: 0.7,
      scale: 0.95,
      transition: {
        repeat: Infinity,
        repeatType: 'reverse' as const,
        duration: 1,
      },
    },
  }), []);

  return { variants, controls };
};

// Gesture animation hook
export const useGestureAnimation = () => {
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();

  const gestureProps = useMemo(() => {
    if (!shouldAnimateValue) return {};

    return {
      whileHover: { scale: 1.02, transition: { duration: 0.2 } },
      whileTap: { scale: 0.98, transition: { duration: 0.1 } },
      whileFocus: { scale: 1.01, transition: { duration: 0.2 } },
    };
  }, [shouldAnimateValue]);

  return gestureProps;
};

// Spring animation hook
export const useSpringAnimation = (
  isActive: boolean,
  springConfig = { damping: 20, stiffness: 300 }
) => {
  const controls = useAnimation();
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();

  useEffect(() => {
    if (!shouldAnimateValue) return;

    if (isActive) {
      controls.start({
        scale: 1.05,
        transition: { type: 'spring', ...springConfig },
      });
    } else {
      controls.start({
        scale: 1,
        transition: { type: 'spring', ...springConfig },
      });
    }
  }, [isActive, controls, springConfig, shouldAnimateValue]);

  return controls;
};

// Auto-animate list hook
export const useAutoAnimateList = <T extends { id: string | number }>(
  items: T[],
  dependencies: any[] = []
) => {
  const { shouldAnimate: shouldAnimateValue } = useEnhancedAnimation();
  const previousItems = useRef<T[]>([]);

  const animationProps = useMemo(() => {
    if (!shouldAnimateValue) return {};

    return {
      layout: true,
      initial: { opacity: 0, scale: 0.8 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.8 },
      transition: {
        type: 'spring',
        damping: 20,
        stiffness: 300,
      },
    };
  }, [shouldAnimateValue]);

  useEffect(() => {
    previousItems.current = items;
  }, [items, ...dependencies]);

  return animationProps;
};