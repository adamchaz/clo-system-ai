/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * Animation Variants - Framer Motion Configurations
 * 
 * Comprehensive collection of animation variants for consistent motion design:
 * - Page transitions (slide, fade, zoom)
 * - Component entrances (stagger, bounce, spring)
 * - Interactive states (hover, tap, focus)
 * - Loading and skeleton animations
 */

import { Variants, Transition } from 'framer-motion';

// Base transitions for consistent timing
export const transitions = {
  smooth: {
    type: 'spring',
    damping: 25,
    stiffness: 120,
  } as Transition,
  
  bouncy: {
    type: 'spring',
    damping: 12,
    stiffness: 200,
  } as Transition,
  
  quick: {
    duration: 0.2,
    ease: 'easeOut',
  } as Transition,
  
  slow: {
    duration: 0.5,
    ease: 'easeInOut',
  } as Transition,
  
  elastic: {
    type: 'spring',
    damping: 8,
    stiffness: 100,
  } as Transition,
};

// Page transition variants
export const pageVariants: Variants = {
  initial: {
    opacity: 0,
    x: -20,
    scale: 0.98,
  },
  enter: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: transitions.smooth,
  },
  exit: {
    opacity: 0,
    x: 20,
    scale: 0.98,
    transition: transitions.quick,
  },
};

// Slide transition variants
export const slideVariants: Variants = {
  slideLeft: {
    initial: { x: -50, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: 50, opacity: 0 },
  },
  slideRight: {
    initial: { x: 50, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -50, opacity: 0 },
  },
  slideUp: {
    initial: { y: 50, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: -50, opacity: 0 },
  },
  slideDown: {
    initial: { y: -50, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: 50, opacity: 0 },
  },
};

// Fade transition variants
export const fadeVariants: Variants = {
  initial: { opacity: 0 },
  animate: { 
    opacity: 1,
    transition: transitions.smooth,
  },
  exit: { 
    opacity: 0,
    transition: transitions.quick,
  },
};

// Scale variants for cards and modals
export const scaleVariants: Variants = {
  initial: {
    scale: 0.9,
    opacity: 0,
  },
  animate: {
    scale: 1,
    opacity: 1,
    transition: transitions.bouncy,
  },
  exit: {
    scale: 0.9,
    opacity: 0,
    transition: transitions.quick,
  },
  hover: {
    scale: 1.02,
    y: -2,
    transition: transitions.quick,
  },
  tap: {
    scale: 0.98,
    transition: { duration: 0.1 },
  },
};

// Stagger container variants
export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
  exit: {
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
};

// Stagger item variants
export const staggerItem: Variants = {
  initial: {
    y: 20,
    opacity: 0,
  },
  animate: {
    y: 0,
    opacity: 1,
    transition: transitions.smooth,
  },
  exit: {
    y: -20,
    opacity: 0,
    transition: transitions.quick,
  },
};

// Button animation variants
export const buttonVariants: Variants = {
  idle: {
    scale: 1,
    boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
  },
  hover: {
    scale: 1.05,
    boxShadow: '0px 4px 12px rgba(0,0,0,0.15)',
    transition: transitions.quick,
  },
  tap: {
    scale: 0.95,
    boxShadow: '0px 1px 2px rgba(0,0,0,0.1)',
    transition: { duration: 0.1 },
  },
  loading: {
    scale: [1, 1.02, 1],
    transition: {
      repeat: Infinity,
      duration: 1.5,
      ease: 'easeInOut',
    },
  },
};

// Card hover effects
export const cardVariants: Variants = {
  rest: {
    y: 0,
    boxShadow: '0px 2px 8px rgba(0,0,0,0.1)',
  },
  hover: {
    y: -4,
    boxShadow: '0px 8px 24px rgba(0,0,0,0.15)',
    transition: {
      type: 'spring',
      damping: 15,
      stiffness: 200,
    },
  },
  tap: {
    y: -2,
    boxShadow: '0px 4px 12px rgba(0,0,0,0.12)',
    transition: { duration: 0.1 },
  },
};

// List item variants
export const listItemVariants: Variants = {
  initial: {
    x: -10,
    opacity: 0,
  },
  animate: {
    x: 0,
    opacity: 1,
    transition: transitions.smooth,
  },
  exit: {
    x: 10,
    opacity: 0,
    transition: transitions.quick,
  },
  hover: {
    x: 4,
    transition: transitions.quick,
  },
};

// Modal/Dialog variants
export const modalVariants: Variants = {
  initial: {
    scale: 0.8,
    opacity: 0,
    y: 50,
  },
  animate: {
    scale: 1,
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      damping: 25,
      stiffness: 300,
    },
  },
  exit: {
    scale: 0.8,
    opacity: 0,
    y: 50,
    transition: {
      duration: 0.2,
      ease: 'easeIn',
    },
  },
};

// Floating Action Button variants
export const fabVariants: Variants = {
  initial: {
    scale: 0,
    rotate: -45,
  },
  animate: {
    scale: 1,
    rotate: 0,
    transition: {
      type: 'spring',
      damping: 12,
      stiffness: 200,
      delay: 0.5,
    },
  },
  hover: {
    scale: 1.1,
    rotate: 5,
    transition: transitions.quick,
  },
  tap: {
    scale: 0.9,
    transition: { duration: 0.1 },
  },
};

// Loading spinner variants
export const spinnerVariants: Variants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

// Pulse animation for notifications
export const pulseVariants: Variants = {
  animate: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Scroll reveal variants
export const scrollRevealVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 50,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: 'easeOut',
    },
  },
};

// Chart animation variants
export const chartVariants: Variants = {
  initial: {
    pathLength: 0,
    opacity: 0,
  },
  animate: {
    pathLength: 1,
    opacity: 1,
    transition: {
      pathLength: { duration: 2, ease: 'easeInOut' },
      opacity: { duration: 0.5 },
    },
  },
};

// Sidebar toggle variants
export const sidebarVariants: Variants = {
  open: {
    x: 0,
    transition: transitions.smooth,
  },
  closed: {
    x: '-100%',
    transition: transitions.smooth,
  },
};

// Navigation menu variants
export const menuVariants: Variants = {
  closed: {
    opacity: 0,
    y: -10,
    scale: 0.95,
  },
  open: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      damping: 20,
      stiffness: 300,
    },
  },
};