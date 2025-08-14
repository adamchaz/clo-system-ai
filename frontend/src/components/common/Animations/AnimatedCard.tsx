/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * AnimatedCard - Enhanced card component with smooth hover and interaction effects
 * 
 * Features:
 * - Smooth hover animations with elevation changes
 * - Click/tap feedback with spring animations
 * - Stagger support for lists of cards
 * - Configurable hover and click effects
 * - Reduced motion support
 * - Material-UI integration
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardProps, useTheme } from '@mui/material';
import { AnimatedCardProps } from './types';
import { useEnhancedAnimation, useHoverAnimation } from './hooks';
import { cardVariants, staggerItem } from './variants';

const AnimatedCard: React.FC<AnimatedCardProps & CardProps> = ({
  children,
  hoverEffect = true,
  clickEffect = true,
  elevation = true,
  stagger = false,
  index = 0,
  delay = 0,
  duration,
  className,
  sx,
  ...cardProps
}) => {
  const theme = useTheme();
  const { shouldAnimate } = useEnhancedAnimation();
  
  // Custom hover animation variants
  const hoverVariants = {
    rest: {
      y: 0,
      boxShadow: elevation ? theme.shadows[2] : 'none',
      transition: {
        type: 'spring',
        damping: 20,
        stiffness: 300,
      },
    },
    hover: {
      y: hoverEffect ? -4 : 0,
      boxShadow: elevation && hoverEffect ? theme.shadows[8] : (elevation ? theme.shadows[2] : 'none'),
      transition: {
        type: 'spring',
        damping: 15,
        stiffness: 300,
      },
    },
  };

  const { hoverProps } = useHoverAnimation(hoverVariants);

  // Click/tap variants
  const tapVariant = clickEffect ? {
    y: hoverEffect ? -2 : 0,
    scale: 0.98,
    boxShadow: elevation ? theme.shadows[4] : 'none',
    transition: { duration: 0.1 },
  } : undefined;

  // Stagger animation variants
  const staggerVariants = stagger ? staggerItem : undefined;

  if (!shouldAnimate) {
    return (
      <Card
        {...cardProps}
        className={className}
        sx={{
          boxShadow: elevation ? theme.shadows[2] : 'none',
          ...sx,
        }}
      >
        {children}
      </Card>
    );
  }

  return (
    <motion.div
      variants={staggerVariants}
      initial={stagger ? 'initial' : undefined}
      animate={stagger ? 'animate' : undefined}
      exit={stagger ? 'exit' : undefined}
      custom={index}
      transition={{
        delay: delay + (stagger ? index * 0.1 : 0),
        duration: duration || 0.3,
      }}
      {...hoverProps}
      whileTap={tapVariant}
      style={{
        display: 'block',
        width: '100%',
      }}
    >
      <Card
        {...cardProps}
        className={className}
        sx={{
          cursor: clickEffect ? 'pointer' : 'default',
          userSelect: 'none',
          boxShadow: 'inherit', // Use the animated shadow from motion.div
          ...sx,
        }}
        component="div" // Prevent nested interactive elements
      >
        {children}
      </Card>
    </motion.div>
  );
};

export default AnimatedCard;