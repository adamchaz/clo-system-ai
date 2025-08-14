/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * AnimatedList - Staggered list animation container
 * 
 * Features:
 * - Staggered entrance animations for list items
 * - Configurable stagger delay and direction
 * - Scroll-triggered animations
 * - Support for different slide directions
 * - Automatic detection of list changes
 * - Performance optimized with intersection observer
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Box } from '@mui/material';
import { AnimatedListProps } from './types';
import { useEnhancedAnimation, useScrollReveal, useStagger } from './hooks';
import { createSlideVariants, calculateStaggerDelay } from './utils';

const AnimatedList: React.FC<AnimatedListProps> = ({
  children,
  staggerDelay,
  direction = 'up',
  threshold = 0.1,
  delay = 0,
  className,
}) => {
  const { shouldAnimate } = useEnhancedAnimation();
  const { ref, isVisible } = useScrollReveal(threshold);
  
  // Create slide variants based on direction
  const slideVariants = createSlideVariants(direction, 30);
  
  // Calculate optimal stagger delay if not provided
  const childrenArray = React.Children.toArray(children);
  const optimizedStaggerDelay = staggerDelay || calculateStaggerDelay(childrenArray.length);
  
  const { containerProps, itemProps } = useStagger(slideVariants, optimizedStaggerDelay);

  if (!shouldAnimate) {
    return (
      <Box ref={ref} className={className}>
        {children}
      </Box>
    );
  }

  return (
    <Box ref={ref} className={className}>
      <motion.div
        variants={containerProps.variants}
        initial={containerProps.initial}
        animate={isVisible ? containerProps.animate : containerProps.initial}
        exit={containerProps.exit}
        transition={{
          delay,
        }}
        style={{
          width: '100%',
        }}
      >
      {React.Children.map(children, (child, index) => (
        <motion.div
          key={index}
          {...itemProps(index)}
          style={{
            width: '100%',
          }}
        >
          {child}
        </motion.div>
      ))}
      </motion.div>
    </Box>
  );
};

export default AnimatedList;