/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * AnimatedPage - Enhanced page wrapper with smooth transitions
 * 
 * Features:
 * - Multiple transition types (slide, fade, scale, rotate, flip)
 * - Directional slide animations
 * - Reduced motion support
 * - Performance optimized
 * - Customizable timing and easing
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Box } from '@mui/material';
import { AnimatedPageProps } from './types';
import { useEnhancedAnimation } from './hooks';
import { getPageTransitionVariants } from './utils';

const AnimatedPage: React.FC<AnimatedPageProps> = ({
  children,
  transition = 'slide',
  direction = 'right',
  delay = 0,
  duration = 0.3,
  className,
}) => {
  const { shouldAnimate, getTransition } = useEnhancedAnimation();
  
  const variants = getPageTransitionVariants(transition, direction);
  const transitionConfig = getTransition('smooth');

  if (!shouldAnimate) {
    return (
      <Box className={className}>
        {children}
      </Box>
    );
  }

  return (
    <Box className={className} style={{ width: '100%', height: '100%' }}>
      <motion.div
        variants={variants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{
          ...transitionConfig,
          duration,
          delay,
        }}
        style={{
          width: '100%',
          height: '100%',
        }}
      >
        {children}
      </motion.div>
    </Box>
  );
};

export default AnimatedPage;